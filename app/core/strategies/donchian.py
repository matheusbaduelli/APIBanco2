import backtrader as bt
from .base import BaseStrategy

class DonchianBreakoutStrategy(BaseStrategy):
    params = (
        ('entry_period', 20),
        ('exit_period', 10),
        ('atr_period', 14),
    )
    
    def __init__(self):
        super().__init__()
        self.highest = bt.indicators.Highest(self.data.high, period=self.params.entry_period)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.params.exit_period)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
    def strategy_logic(self):
        if not self.position:
            if self.data.close[0] > self.highest[-1]:  # Breakout above highest
                current_price = self.data.close[0]
                stop_price = current_price - (2 * self.atr[0])
                size = self.calculate_position_size(current_price, stop_price)
                if size > 0:
                    self.buy(size=size)
                    self.stop_price = stop_price
        else:
            if self.data.close[0] < self.lowest[-1] or self.data.close[0] <= self.stop_price:
                self.sell(size=self.position.size)