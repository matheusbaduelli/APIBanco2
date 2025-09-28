
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import date, datetime
from enum import Enum

class StrategyType(str, Enum):
    SMA_CROSS = "sma_cross"
    DONCHIAN_BREAKOUT = "donchian_breakout"
    MOMENTUM = "momentum"
    

class BacktestRunRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol (e.g., PETR4.SA)")
    start_date: date
    end_date: date
    strategy_type: StrategyType
    strategy_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    initial_cash: float = Field(default=100000.0, gt=0)
    commission: float = Field(default=0.001, ge=0)
    timeframe: str = Field(default="1d")

class TradeInfo(BaseModel):
    date: date
    side: str
    price: float
    size: float
    commission: float
    pnl: float

class DailyPositionInfo(BaseModel):
    date: date
    position_size: float
    cash: float
    equity: float
    drawdown: float

class MetricsInfo(BaseModel):
    total_return: float
    sharpe: Optional[float]
    max_drawdown: float
    win_rate: Optional[float]
    avg_trade_return: Optional[float]

class BacktestRunResponse(BaseModel):
    id: int
    status: str

class BacktestResultResponse(BaseModel):
    backtest_id: int
    metrics: MetricsInfo
    trades: List[TradeInfo]
    daily_positions: List[DailyPositionInfo]
    equity_curve: List[Dict[str, Any]]

class BacktestListItem(BaseModel):
    id: int
    created_at: datetime
    ticker: str
    strategy_type: str
    start_date: date
    end_date: date
    status: str

class BacktestListResponse(BaseModel):
    items: List[BacktestListItem]
    total: int
    page: int
    page_size: int

class IndicatorUpdateRequest(BaseModel):
    ticker: str

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
