import backtrader as bt
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from .strategies.sma_cross import SMAStrategy
from .strategies.donchian import DonchianBreakoutStrategy
from .strategies.momentum import MomentumStrategy

STRATEGY_MAP = {
    'sma_cross': SMAStrategy,  
    'donchian_breakout': DonchianBreakoutStrategy,
    'momentum': MomentumStrategy
}

class PandasData(bt.feeds.PandasData):
    """Custom Pandas data feed for Backtrader"""
    lines = ('open', 'high', 'low', 'close', 'volume')
    params = (
        ('datetime', None),
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
        ('openinterest', -1),
    )

def run_backtest(df: pd.DataFrame, strategy_type: str, strategy_params: Dict[str, Any], 
                initial_cash: float = 100000.0, commission: float = 0.001) -> Dict[str, Any]:
    """
    Run backtest using Backtrader
    """
    cerebro = bt.Cerebro()
    
    # Set up broker
    cerebro.broker.set_cash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    
    # Add data feed
    data = PandasData(dataname=df)
    cerebro.adddata(data)
    
    # Add strategy
    strategy_class = STRATEGY_MAP.get(strategy_type)
    if not strategy_class:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    cerebro.addstrategy(strategy_class, **strategy_params)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # Run backtest
    results = cerebro.run()
    strategy_instance = results[0]
    
    final_value = cerebro.broker.getvalue()
    total_return = (final_value - initial_cash) / initial_cash
    
    # Extract metrics
    sharpe = strategy_instance.analyzers.sharpe.get_analysis().get('sharperatio', None)
    drawdown = strategy_instance.analyzers.drawdown.get_analysis()
    trades_analysis = strategy_instance.analyzers.trades.get_analysis()
    
    return {
        'final_cash': final_value,
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': drawdown.get('max', {}).get('drawdown', 0) / 100,
        'trades': strategy_instance.trades_list,
        'daily_positions': strategy_instance.daily_positions,
        'win_rate': trades_analysis.get('won', {}).get('total', 0) / max(trades_analysis.get('total', {}).get('total', 1), 1),
        'avg_trade_return': trades_analysis.get('pnl', {}).get('gross', {}).get('average', 0)
    }
