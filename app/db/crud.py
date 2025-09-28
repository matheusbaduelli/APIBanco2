from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Tuple, Optional
from datetime import date
from . import models
import json

def create_backtest(db: Session, obj_in: dict):
    """Criar novo backtest"""
    obj = models.Backtest(
        ticker=obj_in.get('ticker'),
        start_date=obj_in.get('start_date'),
        end_date=obj_in.get('end_date'),
        strategy_type=obj_in.get('strategy_type'),
        strategy_params_json=json.dumps(obj_in.get('strategy_params_json', {})),
        initial_cash=obj_in.get('initial_cash'),
        commission=obj_in.get('commission'),
        status=obj_in.get('status', 'pending')
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_backtest_status(db: Session, backtest_id: int, status: str, message: str = None):
    """Atualizar status do backtest"""
    backtest = db.query(models.Backtest).filter(models.Backtest.id == backtest_id).first()
    if backtest:
        backtest.status = status
        if message:
           
            pass
        db.commit()
        return backtest
    return None

def store_backtest_results(db: Session, backtest_id: int, results: dict):
    """Armazenar resultados completos do backtest"""
    
    
    for trade_data in results.get('trades', []):
        trade = models.Trade(
            backtest_id=backtest_id,
            date=trade_data['date'],
            side=trade_data['side'],
            price=trade_data['price'],
            size=trade_data['size'],
            commission=trade_data.get('commission', 0),
            pnl=trade_data.get('pnl', 0)
        )
        db.add(trade)
    
    
    for pos_data in results.get('daily_positions', []):
        position = models.DailyPosition(
            backtest_id=backtest_id,
            date=pos_data['date'],
            position_size=pos_data['position_size'],
            cash=pos_data['cash'],
            equity=pos_data['equity'],
            drawdown=pos_data.get('drawdown', 0)
        )
        db.add(position)
    
   
    metrics = models.Metrics(
        backtest_id=backtest_id,
        total_return=results.get('total_return', 0),
        sharpe=results.get('sharpe'),
        max_drawdown=results.get('max_drawdown', 0),
        win_rate=results.get('win_rate'),
        avg_trade_return=results.get('avg_trade_return')
    )
    db.add(metrics)
    
    db.commit()

def get_backtest_with_results(db: Session, backtest_id: int):
    """Obter backtest com todos os resultados"""
    return (db.query(models.Backtest)
            .filter(models.Backtest.id == backtest_id)
            .first())

def get_backtests_paginated(db: Session, page: int, page_size: int, 
                           ticker: Optional[str] = None, 
                           strategy_type: Optional[str] = None) -> Tuple[List[models.Backtest], int]:
    """Listar backtests com paginação e filtros"""
    query = db.query(models.Backtest)
    
    if ticker:
        query = query.filter(models.Backtest.ticker.ilike(f"%{ticker}%"))
    if strategy_type:
        query = query.filter(models.Backtest.strategy_type == strategy_type)
    
    total = query.count()
    backtests = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return backtests, total