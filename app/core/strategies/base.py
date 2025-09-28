import backtrader as bt
import pandas as pd
from abc import ABCMeta, abstractmethod
from typing import Dict, Any

# 🔹 Metaclass combinada (ABCMeta + metaclass de bt.Strategy)
class StrategyABCMeta(ABCMeta, type(bt.Strategy)):
    pass

class BaseStrategy(bt.Strategy, metaclass=StrategyABCMeta):
    """Base class for all trading strategies"""
    
    def __init__(self):
        super().__init__()
        self.trades_list = []
        self.daily_positions = []
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades_list.append({
                'date': self.datas[0].datetime.date(0),
                'side': 'SELL' if trade.size < 0 else 'BUY',
                'price': trade.price,
                'size': abs(trade.size),
                'commission': trade.commission,
                'pnl': trade.pnl
            })
    
    def next(self):
        self.daily_positions.append({
            'date': self.datas[0].datetime.date(0),
            'position_size': self.position.size,
            'cash': self.broker.get_cash(),
            'equity': self.broker.get_value(),
            'drawdown': 0.0  
        })
        self.strategy_logic()
    
    @abstractmethod
    def strategy_logic(self):
        """Implement specific strategy logic here"""
        pass
    
    def calculate_position_size(self, price: float, stop_price: float) -> int:
        """Calculate position size based on 1% risk rule"""
        risk_per_trade = self.broker.get_value() * 0.01 
        risk_per_share = abs(price - stop_price)
        if risk_per_share == 0:
            return 0
        position_size = int(risk_per_trade / risk_per_share)
        max_affordable = int(self.broker.get_cash() / price)
        return min(position_size, max_affordable)
