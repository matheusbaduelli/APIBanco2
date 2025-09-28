import backtrader as bt
from .base import BaseStrategy

class SMAStrategy(BaseStrategy): 
    """Estratégia de cruzamento de médias móveis simples"""
    params = (
        ('fast', 20),
        ('slow', 50),
        ('atr_period', 14),
    )
    
    def __init__(self):
        super().__init__()
        self.sma_fast = bt.indicators.SMA(self.data.close, period=self.params.fast)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=self.params.slow)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        self.stop_price = None
        
    def strategy_logic(self):
        if not self.position:
            if self.crossover > 0:
                current_price = self.data.close[0]
                stop_price = current_price - (2 * self.atr[0])
                size = self.calculate_position_size(current_price, stop_price)
                if size > 0:
                    self.buy(size=size)
                    self.stop_price = stop_price
        else:
            if self.crossover < 0 or self.data.close[0] <= self.stop_price:
                self.sell(size=self.position.size)
                self.stop_price = None