import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date

from app.core.backtest_engine import run_backtest

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
    # 🔹 CORREÇÃO: Drawdown deve ser <= 0 (negativo ou zero)
    assert results['max_drawdown'] <= 0