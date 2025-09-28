import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date

@pytest.fixture
def sample_market_data():
    """Dados de mercado para testes"""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    
    # Gerar dados realistas
    np.random.seed(42)  
    prices = []
    base_price = 100
    for i in range(100):
        change = np.random.normal(0.001, 0.02)  
        base_price = base_price * (1 + change)
        prices.append(base_price)
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * 1.01 for p in prices],
        'Low': [p * 0.99 for p in prices],
        'Close': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'Volume': [int(abs(np.random.normal(10000, 2000))) for _ in prices]
    }, index=dates)
    
    return df

@pytest.fixture  
def trending_data():
    """Dados com tendência ascendente clara para testar estratégias"""
    dates = pd.date_range('2020-01-01', periods=60, freq='D')
    
    # Tendência ascendente mais pronunciada
    np.random.seed(42)
    base_prices = np.linspace(100, 180, 60)  # +80% de crescimento
    noise = np.random.normal(0, 1, 60)  
    prices = base_prices + noise
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices], 
        'Close': [p * 1.005 for p in prices],  # Ligeiro bias positivo
        'Volume': [1000] * 60
    }, index=dates)
    
    return df

@pytest.fixture
def sample_data(sample_market_data):
    """🔹 FIXTURE OBRIGATÓRIA - era esta que estava faltando"""
    return sample_market_data