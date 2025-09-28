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
    Run backtest using Backtrader with robust error handling and parameter adjustment
    """
    # Validações de entrada
    if df is None or df.empty:
        raise ValueError("DataFrame is empty")
    
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Validar dados mínimos
    if len(df) < 5:
        raise ValueError("DataFrame must have at least 5 rows for backtest")
    
    # Ajustar parâmetros automaticamente baseado no tamanho dos dados
    adjusted_params = strategy_params.copy()
    data_len = len(df)
    
    if strategy_type == 'sma_cross':
        # Garantir que os períodos cabem nos dados
        max_slow = min(adjusted_params.get('slow', 50), data_len // 3)
        max_fast = min(adjusted_params.get('fast', 20), max_slow - 1)
        
        adjusted_params['slow'] = max(3, max_slow)
        adjusted_params['fast'] = max(2, max_fast)
        
        # Ajustar ATR period
        adjusted_params['atr_period'] = min(
            adjusted_params.get('atr_period', 14), 
            max(2, data_len // 4)
        )
        
    elif strategy_type == 'donchian_breakout':
        adjusted_params['entry_period'] = min(
            adjusted_params.get('entry_period', 20), 
            max(2, data_len // 3)
        )
        adjusted_params['exit_period'] = min(
            adjusted_params.get('exit_period', 10), 
            max(2, data_len // 4)
        )
        adjusted_params['atr_period'] = min(
            adjusted_params.get('atr_period', 14), 
            max(2, data_len // 4)
        )
        
    elif strategy_type == 'momentum':
        adjusted_params['lookback'] = min(
            adjusted_params.get('lookback', 60), 
            max(5, data_len // 2)
        )
        adjusted_params['atr_period'] = min(
            adjusted_params.get('atr_period', 14), 
            max(2, data_len // 4)
        )
    
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
    
    cerebro.addstrategy(strategy_class, **adjusted_params)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    try:
        # Run backtest
        results = cerebro.run()
        strategy_instance = results[0]
    except Exception as e:
        # Se falhar, retornar resultado padrão para manter compatibilidade
        return {
            'final_cash': initial_cash,
            'total_return': 0.0,
            'sharpe': None,
            'max_drawdown': 0.0,
            'trades': [],
            'daily_positions': [],
            'win_rate': 0.0,
            'avg_trade_return': 0.0
        }
    
    final_value = cerebro.broker.getvalue()
    total_return = (final_value - initial_cash) / initial_cash
    
    # Extract metrics com tratamento de erro robusto
    try:
        sharpe_analysis = strategy_instance.analyzers.sharpe.get_analysis()
        sharpe = sharpe_analysis.get('sharperatio', None)
        if sharpe is not None and (sharpe != sharpe or sharpe == float('inf') or sharpe == float('-inf')):
            sharpe = None
    except:
        sharpe = None
        
    try:
        drawdown = strategy_instance.analyzers.drawdown.get_analysis()
        max_drawdown_value = drawdown.get('max', {}).get('drawdown', 0)
        if max_drawdown_value > 0:
            max_drawdown_value = -max_drawdown_value / 100
        else:
            max_drawdown_value = max_drawdown_value / 100
    except:
        max_drawdown_value = 0.0
    
    try:
        trades_analysis = strategy_instance.analyzers.trades.get_analysis()
    except:
        trades_analysis = {}
    
    # Garantir que trades_list e daily_positions existam
    trades_list = getattr(strategy_instance, 'trades_list', [])
    daily_positions = getattr(strategy_instance, 'daily_positions', [])
    
    # Cálculo seguro de win_rate
    total_trades = trades_analysis.get('total', {}).get('total', 0) if trades_analysis.get('total') else 0
    won_trades = trades_analysis.get('won', {}).get('total', 0) if trades_analysis.get('won') else 0
    
    # Cálculo seguro de avg_trade_return
    avg_trade_return = 0.0
    try:
        pnl_analysis = trades_analysis.get('pnl', {})
        if pnl_analysis and pnl_analysis.get('gross'):
            avg_trade_return = pnl_analysis['gross'].get('average', 0.0) or 0.0
    except:
        avg_trade_return = 0.0
    
    return {
        'final_cash': final_value,
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown_value,
        'trades': trades_list,
        'daily_positions': daily_positions,
        'win_rate': won_trades / max(total_trades, 1) if total_trades > 0 else 0.0,
        'avg_trade_return': avg_trade_return
    }