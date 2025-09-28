import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch, Mock
import pandas as pd
import numpy as np
from datetime import datetime, date

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db import models

# Configurar banco de dados em memória para testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Sobrescrever a dependência do banco para usar banco em memória"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Aplicar override da dependência
app.dependency_overrides[get_db] = override_get_db

# Cliente de teste
client = TestClient(app)

@pytest.fixture
def mock_yfinance_data():
    """Dados fictícios que simulariam retorno do yfinance"""
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    np.random.seed(42)
    
    prices = []
    base_price = 100
    for i in range(30):
        change = np.random.normal(0.001, 0.02)
        base_price = base_price * (1 + change)
        prices.append(base_price)
    
    return pd.DataFrame({
        'Open': prices,
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Close': [p * 1.01 for p in prices],
        'Volume': [1000] * 30
    }, index=dates)

@pytest.fixture(scope="function")
def setup_database():
    """Criar tabelas antes de cada teste"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestUpdateIndicators:
    """Testes para o endpoint POST /data/indicators/update"""
    
    def test_update_indicators_success(self, setup_database, mock_yfinance_data):
        """Teste de sucesso na atualização de indicadores"""
        
        with patch('app.services.yfinance_client.yf.download') as mock_download:
            mock_download.return_value = mock_yfinance_data
            
            response = client.post(
                "/data/indicators/update",
                json={"ticker": "AAPL"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert data["ticker"] == "AAPL"
            assert data["records_updated"] == 30
            assert "Indicators updated for AAPL" in data["message"]
    
    def test_update_indicators_no_data_found(self, setup_database):
        """Teste quando não há dados disponíveis para o ticker"""
        
        with patch('app.services.yfinance_client.yf.download') as mock_download:
            mock_download.return_value = pd.DataFrame()
            
            response = client.post(
                "/data/indicators/update",
                json={"ticker": "INVALID"}
            )
            
            assert response.status_code == 404
            assert "No data found for ticker" in response.json()["detail"]
    
    def test_update_indicators_invalid_ticker_format(self, setup_database):
        """Teste com formato inválido de ticker"""
        
        response = client.post(
            "/data/indicators/update",
            json={"ticker": ""}  # Ticker vazio
        )
        
        assert response.status_code == 422
    
    def test_update_indicators_missing_ticker(self, setup_database):
        """Teste sem fornecer o campo ticker"""
        
        response = client.post(
            "/data/indicators/update",
            json={}  # Sem ticker
        )
        
        assert response.status_code == 422
        assert "ticker" in str(response.json()["detail"])
    
    def test_update_indicators_yfinance_error(self, setup_database):
        """Teste quando yfinance retorna erro"""
        
        with patch('app.services.yfinance_client.yf.download') as mock_download:
            mock_download.side_effect = Exception("Yahoo Finance API error")
            
            response = client.post(
                "/data/indicators/update",
                json={"ticker": "AAPL"}
            )
            
            assert response.status_code == 500
            assert "Yahoo Finance API error" in response.json()["detail"]
    
    def test_update_indicators_valid_ticker_formats(self, setup_database, mock_yfinance_data):
        """Teste com diferentes formatos válidos de ticker"""
        
        valid_tickers = ["AAPL", "PETR4.SA", "TSLA"]
        
        for ticker in valid_tickers:
            with patch('app.services.yfinance_client.yf.download') as mock_download:
                mock_download.return_value = mock_yfinance_data
                
                response = client.post(
                    "/data/indicators/update",
                    json={"ticker": ticker}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["ticker"] == ticker
                assert data["status"] == "success"

class TestHealthEndpoint:
    """Testes para o endpoint de health"""
    
    def test_health_check_success(self, setup_database):
        """Teste do endpoint de health com sucesso"""
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["ok", "error"]
        assert data["database"] in ["connected", "disconnected"]
        assert "timestamp" in data

class TestBacktestEndpoints:
    """Testes básicos dos endpoints de backtest"""
    
    def test_list_backtests_empty(self, setup_database):
        """Teste de listagem sem backtests"""
        
        response = client.get("/backtests")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    def test_get_nonexistent_backtest_results(self, setup_database):
        """Teste de busca de resultados de backtest inexistente"""
        
        response = client.get("/backtests/99999/results")
        
        assert response.status_code == 404
        assert "Backtest not found" in response.json()["detail"]

# Testes de integração mais realistas
class TestIntegrationRealDatabase:
    """Testes que verificam a integração real com components"""
    
    def test_create_symbol_and_update_indicators(self, setup_database, mock_yfinance_data):
        """Teste que verifica criação de símbolo e atualização de indicadores"""
        
        with patch('app.services.yfinance_client.yf.download') as mock_download:
            mock_download.return_value = mock_yfinance_data
            
            # Primeira chamada - deve criar o símbolo
            response1 = client.post(
                "/data/indicators/update",
                json={"ticker": "NEW_TICKER"}
            )
            
            assert response1.status_code == 200
            assert response1.json()["ticker"] == "NEW_TICKER"
            
            # Segunda chamada - deve usar o símbolo existente
            response2 = client.post(
                "/data/indicators/update",
                json={"ticker": "NEW_TICKER"}
            )
            
            assert response2.status_code == 200
            assert response2.json()["ticker"] == "NEW_TICKER"
            
            # Verificar que o símbolo foi criado no banco
            db = TestingSessionLocal()
            try:
                symbol = db.query(models.Symbol).filter(
                    models.Symbol.ticker == "NEW_TICKER"
                ).first()
                assert symbol is not None
                assert symbol.ticker == "NEW_TICKER"
            finally:
                db.close()

# Testes de performance
class TestPerformance:
    """Testes básicos de performance"""
    
    def test_update_indicators_response_time(self, setup_database, mock_yfinance_data):
        """Teste de tempo de resposta"""
        import time
        
        with patch('app.services.yfinance_client.yf.download') as mock_download:
            mock_download.return_value = mock_yfinance_data
            
            start_time = time.time()
            
            response = client.post(
                "/data/indicators/update",
                json={"ticker": "AAPL"}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response_time < 2.0  # Menos de 2 segundos
            assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])