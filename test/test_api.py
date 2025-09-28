from unittest.mock import MagicMock, patch, AsyncMock,ANY
from fastapi.testclient import TestClient
from app.main import app  # seu FastAPI app
import pytest
from datetime import datetime, date
from app.Api.schemas import StrategyType 

client = TestClient(app)

from app.Api.routes import get_db as original_get_db

def test_health_check_connected_override():
    mock_db = MagicMock()
    mock_db.execute.return_value = 1

    app.dependency_overrides[original_get_db] = lambda: mock_db
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    app.dependency_overrides.clear()


def test_list_backtests():
    # Mock de backtests retornados pelo CRUD
    mock_backtest1 = MagicMock()
    mock_backtest1.id = 1
    mock_backtest1.created_at = datetime(2023, 1, 1, 10, 0)
    mock_backtest1.ticker = "AAPL"
    mock_backtest1.strategy_type = "mock_strategy"
    mock_backtest1.start_date = date(2023, 1, 1)
    mock_backtest1.end_date = date(2023, 1, 10)
    mock_backtest1.status = "completed"

    mock_backtest2 = MagicMock()
    mock_backtest2.id = 2
    mock_backtest2.created_at = datetime(2023, 2, 1, 11, 0)
    mock_backtest2.ticker = "GOOG"
    mock_backtest2.strategy_type = "mock_strategy"
    mock_backtest2.start_date = date(2023, 2, 1)
    mock_backtest2.end_date = date(2023, 2, 10)
    mock_backtest2.status = "running"

    mock_backtests = [mock_backtest1, mock_backtest2]
    total_count = 2

    # Mock da função get_backtests_paginated
    with patch("app.Api.routes.crud.get_backtests_paginated", return_value=(mock_backtests, total_count)) as mock_get_backtests, \
         patch("app.Api.routes.get_db"):

        # Chamada do endpoint sem filtros (defaults)
        response = client.get("/backtests")
        assert response.status_code == 200
        data = response.json()

        # Verifica informações gerais
        assert data["total"] == total_count
        assert data["page"] == 1
        assert data["page_size"] == 10

        # Verifica itens
        assert len(data["items"]) == 2
        assert data["items"][0]["id"] == 1
        assert data["items"][0]["ticker"] == "AAPL"
        assert data["items"][0]["strategy_type"] == "mock_strategy"
        assert data["items"][0]["status"] == "completed"
        assert data["items"][1]["id"] == 2
        assert data["items"][1]["ticker"] == "GOOG"
        assert data["items"][1]["status"] == "running"

        # Confirma que a função CRUD foi chamada com os parâmetros corretos, ignorando o objeto do DB
        mock_get_backtests.assert_called_once_with(ANY, 1, 10, None, None)


def test_update_indicators_success():
    mock_df = [1, 2, 3]  # simula dados retornados

    with patch("app.Api.routes.download_and_store_data", return_value=mock_df) as mock_download, \
         patch("app.Api.routes.get_db"):

        payload = {"ticker": "AAPL"}
        response = client.post("/data/indicators/update", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Verifica conteúdo da resposta
        assert data["status"] == "success"
        assert data["ticker"] == "AAPL"
        assert data["records_updated"] == len(mock_df)
        assert "Indicators updated for AAPL" in data["message"]

        # Confirma que a função foi chamada
        assert mock_download.called


def test_update_indicators_no_data():
    with patch("app.Api.routes.download_and_store_data", new_callable=AsyncMock, return_value=None), \
         patch("app.Api.routes.get_db", return_value=MagicMock()):
        
        payload = {"ticker": "INVALID"}
        response = client.post("/data/indicators/update", json=payload)

        # Deve retornar erro 404
        assert response.status_code == 404
        assert response.json()["detail"] == "No data found for ticker"