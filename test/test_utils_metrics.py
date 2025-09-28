import pandas as pd
import numpy as np
import pytest
from app.utils.metrics import sharpe_ratio,max_drawdown    # ajuste o caminho conforme seu projeto

def test_sharpe_ratio_with_valid_list():
    returns = [0.01, 0.02, 0.015, 0.03, -0.005]
    result = sharpe_ratio(returns)
    assert isinstance(result, float)
    assert result != 0

def test_sharpe_ratio_with_valid_series():
    returns = pd.Series([0.01, 0.02, -0.01, 0.005, 0.015])
    result = sharpe_ratio(returns, risk_free_rate=0.02, periods=252)
    assert isinstance(result, float)

def test_sharpe_ratio_with_nan_values():
    returns = pd.Series([0.01, np.nan, 0.015, np.nan, 0.02])
    result = sharpe_ratio(returns)
    assert result is not None  # deve ignorar NaN

def test_sharpe_ratio_empty_returns():
    returns = pd.Series([])
    result = sharpe_ratio(returns)
    assert result is None

def test_sharpe_ratio_zero_std():
    returns = pd.Series([0.01, 0.01, 0.01])  # desvio padrão = 0
    result = sharpe_ratio(returns)
    assert result is None

def test_sharpe_ratio_invalid_input():
    result = sharpe_ratio("not a series")
    assert result is None


def test_max_drawdown_with_valid_series():
    equity = pd.Series([100, 120, 80, 90, 150, 130])
    result = max_drawdown(equity)
    # drawdown mais profundo: de 120 para 80 = -33.33%
    assert pytest.approx(result, 0.01) == -0.3333

def test_max_drawdown_with_list_input():
    equity = [100, 110, 105, 90, 95]
    result = max_drawdown(equity)
    assert isinstance(result, float)

def test_max_drawdown_no_drawdown():
    equity = pd.Series([100, 110, 120, 130])  # só sobe
    result = max_drawdown(equity)
    assert result == 0  # nunca caiu do pico

def test_max_drawdown_with_nan_values():
    equity = pd.Series([100, np.nan, 120, 90, np.nan, 80])
    result = max_drawdown(equity)
    assert result <= 0  # deve retornar drawdown válido (negativo ou zero)

def test_max_drawdown_empty_series():
    equity = pd.Series([])
    result = max_drawdown(equity)
    assert result is None or (isinstance(result, float) and np.isnan(result))


def test_max_drawdown_invalid_input():
    result = max_drawdown("not a series")
    assert result is None