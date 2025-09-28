import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from app.core.backtest_engine import run_backtest  # ✅ FUNÇÃO CORRETA

def test_sma_backtest_basic():
    """Teste básico da estratégia SMA Cross"""
    # Criar dados sintéticos
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    
    # Gerar preços com tendência
    np.random.seed(42)  # Para reprodutibilidade
    base_price = 100
    returns = np.random.normal(0.001, 0.02, 100)  # 0.1% retorno médio, 2% vol
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # Criar DataFrame no formato esperado pelo Backtrader
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * 1.01 for p in prices],  # High 1% acima
        'Low': [p * 0.99 for p in prices],   # Low 1% abaixo  
        'Close': prices,
        'Volume': [1000] * 100
    }, index=dates)
    
    # Executar backtest
    results = run_backtest(
        df=df,
        strategy_type='sma_cross',
        strategy_params={'fast': 5, 'slow': 20},
        initial_cash=10000.0,
        commission=0.001
    )
    
    # Validar resultados
    assert 'final_cash' in results
    assert 'total_return' in results
    assert 'trades' in results
    assert 'daily_positions' in results
    assert isinstance(results['final_cash'], float)
    assert results['final_cash'] > 0
    assert isinstance(results['total_return'], float)

def test_donchian_strategy():
    """Teste da estratégia Donchian Breakout"""
    dates = pd.date_range('2020-01-01', periods=50, freq='D')
    
    # Criar padrão de breakout
    prices = list(range(90, 140))  # Tendência ascendente clara
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * 1.005 for p in prices],
        'Low': [p * 0.995 for p in prices],
        'Close': prices,
        'Volume': [2000] * 50
    }, index=dates)
    
    results = run_backtest(
        df=df,
        strategy_type='donchian_breakout', 
        strategy_params={'entry_period': 20, 'exit_period': 10},
        initial_cash=50000.0,
        commission=0.0005
    )
    
    assert results['final_cash'] > 0
    assert 'max_drawdown' in results
    assert results['max_drawdown'] <= 0  # Drawdown é negativo

def test_momentum_strategy():
    """Teste da estratégia Momentum"""
    dates = pd.date_range('2020-01-01', periods=120, freq='D')  # Mais dados para momentum
    
    # Criar momentum positivo
    base = 100
    momentum_prices = [base + i * 0.5 for i in range(120)]  # Tendência constante
    
    df = pd.DataFrame({
        'Open': momentum_prices,
        'High': [p * 1.01 for p in momentum_prices],
        'Low': [p * 0.99 for p in momentum_prices],
        'Close': momentum_prices, 
        'Volume': [1500] * 120
    }, index=dates)
    
    results = run_backtest(
        df=df,
        strategy_type='momentum',
        strategy_params={'lookback': 60, 'percentile_threshold': 70},
        initial_cash=25000.0,
        commission=0.002
    )
    
    assert results['final_cash'] > 0
    assert 'sharpe' in results
    # Sharpe pode ser None se não houve trades suficientes
    if results['sharpe'] is not None:
        assert isinstance(results['sharpe'], (int, float))