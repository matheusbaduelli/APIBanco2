from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime


from .base import Base

class Symbol(Base):
    __tablename__ = 'symbols'
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True)
    name = Column(String)
    exchange = Column(String)
    currency = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

class Price(Base):
    __tablename__ = 'prices'
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id'))
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    
    __table_args__ = (UniqueConstraint('symbol_id', 'date'),)
    symbol = relationship("Symbol")

class Indicator(Base):
    __tablename__ = 'indicators'
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id'))
    date = Column(Date, index=True)
    name = Column(String)
    value = Column(Float)
    params_hash = Column(String)
    
    __table_args__ = (UniqueConstraint('symbol_id', 'date', 'name', 'params_hash'),)
    symbol = relationship("Symbol")

class Backtest(Base):
    __tablename__ = 'backtests'
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    ticker = Column(String, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    strategy_type = Column(String)
    strategy_params_json = Column(Text)
    initial_cash = Column(Float)
    commission = Column(Float)
    status = Column(String, default='pending')

    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")
    daily_positions = relationship("DailyPosition", back_populates="backtest", cascade="all, delete-orphan")
    metrics = relationship("Metrics", back_populates="backtest", uselist=False, cascade="all, delete-orphan")

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey('backtests.id'))
    date = Column(Date)
    side = Column(String)  # BUY/SELL
    price = Column(Float)
    size = Column(Float)
    commission = Column(Float)
    pnl = Column(Float)
    
    backtest = relationship("Backtest", back_populates="trades")

class DailyPosition(Base):
    __tablename__ = 'daily_positions'
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey('backtests.id'))
    date = Column(Date)
    position_size = Column(Float)
    cash = Column(Float)
    equity = Column(Float)
    drawdown = Column(Float)

    backtest = relationship("Backtest", back_populates="daily_positions")

class Metrics(Base):
    __tablename__ = 'metrics'
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey('backtests.id'), unique=True)
    total_return = Column(Float)
    sharpe = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    avg_trade_return = Column(Float)

    backtest = relationship("Backtest", back_populates="metrics")

class JobRun(Base):
    __tablename__ = 'job_runs'
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    status = Column(String)
    message = Column(Text)