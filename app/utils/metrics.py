import numpy as np
import pandas as pd
from typing import List

def sharpe_ratio(returns, risk_free_rate: float = 0.0, periods: int = 252):
    """Calcular Sharpe Ratio"""
    if isinstance(returns, list):
        returns = pd.Series(returns)
    
    try:
        returns_clean = returns.dropna()
        if len(returns_clean) == 0 or returns_clean.std() == 0:
            return None
        
        excess_return = returns_clean.mean() - risk_free_rate / periods
        return (excess_return / returns_clean.std()) * np.sqrt(periods)
    except Exception:
        return None

def max_drawdown(equity_series):
    """Calcular drawdown máximo"""
    if isinstance(equity_series, list):
        equity_series = pd.Series(equity_series)
    
    try:
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        return drawdown.min()
    except Exception:
        return None

def calculate_drawdown_series(equity_values: List[float]) -> List[float]:
    """Calcular série de drawdowns"""
    if not equity_values:
        return []
    
    equity_series = pd.Series(equity_values)
    peak = equity_series.expanding().max()
    drawdown_series = (equity_series - peak) / peak
    
    return drawdown_series.fillna(0).tolist()

def calculate_win_rate(trades: List[dict]) -> float:
    """Calcular taxa de acerto"""
    if not trades:
        return 0.0
    
    winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
    return winning_trades / len(trades)

def calculate_avg_trade_return(trades: List[dict]) -> float:
    """Calcular retorno médio por trade"""
    if not trades:
        return 0.0
    
    total_pnl = sum(trade.get('pnl', 0) for trade in trades)
    return total_pnl / len(trades)
