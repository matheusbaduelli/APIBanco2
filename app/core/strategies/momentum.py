import backtrader as bt
from .base import BaseStrategy

class MomentumStrategy(BaseStrategy):
    params = (
        ('lookback', 60),
        ('percentile_threshold', 70),
        ('atr_period', 14),
    )
    
    def __init__(self):
        super().__init__()
        self.returns = bt.indicators.ROC(self.data.close, period=self.params.lookback)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.returns_history = []
        
    def strategy_logic(self):
        
        if len(self.returns_history) >= 252:  
            self.returns_history.pop(0)
        self.returns_history.append(self.returns[0])
        
        if len(self.returns_history) < 60:
            return
            
        
        sorted_returns = sorted(self.returns_history)
        threshold_idx = int(len(sorted_returns) * self.params.percentile_threshold / 100)
        threshold = sorted_returns[threshold_idx]
        
        if not self.position:
            if self.returns[0] > threshold and self.returns[0] > 0:
                current_price = self.data.close[0]
                stop_price = current_price - (2 * self.atr[0])
                size = self.calculate_position_size(current_price, stop_price)
                if size > 0:
                    self.buy(size=size)
                    self.stop_price = stop_price
        else:
            if self.returns[0] < 0 or self.data.close[0] <= self.stop_price:
                self.sell(size=self.position.size)