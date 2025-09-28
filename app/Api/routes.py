from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
from datetime import datetime, timedelta

from . import schemas
from ..db.session import get_db
from ..db import crud
from ..services.yfinance_client import download_and_store_data
from ..core.backtest_engine import run_backtest
from ..utils.metrics import calculate_drawdown_series

router = APIRouter()

@router.get('/health', response_model=schemas.HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return schemas.HealthResponse(
        status="ok" if db_status == "connected" else "error",
        database=db_status,
        timestamp=datetime.utcnow()
    )

@router.post('/backtests/run', response_model=schemas.BacktestRunResponse)
async def run_backtest_endpoint(
    request: schemas.BacktestRunRequest,
    db: Session = Depends(get_db)
):
    try:
        
        backtest = crud.create_backtest(db, {
            "ticker": request.ticker,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "strategy_type": request.strategy_type,
            "strategy_params_json": request.strategy_params,
            "initial_cash": request.initial_cash,
            "commission": request.commission,
            "status": "running"
        })
        
        
        asyncio.create_task(execute_backtest(backtest.id, request, db))
        
        
        return schemas.BacktestRunResponse(
            id=backtest.id,
            status="running"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def execute_backtest(backtest_id: int, request: schemas.BacktestRunRequest, db: Session):
    """Execute backtest asynchronously"""
    try:
        
        df = await download_and_store_data(request.ticker, request.start_date, request.end_date, db)
        
        if df is None or df.empty:
            crud.update_backtest_status(db, backtest_id, "failed", "No data found")
            return
        
        
        results = run_backtest(
            df, 
            request.strategy_type, 
            request.strategy_params,
            request.initial_cash,
            request.commission
        )
        
        
        crud.store_backtest_results(db, backtest_id, results)
        crud.update_backtest_status(db, backtest_id, "completed")
        
    except Exception as e:
        crud.update_backtest_status(db, backtest_id, "failed", str(e))

@router.get('/backtests/{backtest_id}/results', response_model=schemas.BacktestResultResponse)
def get_backtest_results(backtest_id: int, db: Session = Depends(get_db)):
    backtest = crud.get_backtest_with_results(db, backtest_id)
    
    if not backtest:
        raise HTTPException(404, "Backtest not found")
    
    if backtest.status != "completed":
        raise HTTPException(400, f"Backtest status: {backtest.status}")
    
    
    daily_positions = calculate_drawdown_series([pos.equity for pos in backtest.daily_positions])
    
    return schemas.BacktestResultResponse(
        backtest_id=backtest.id,
        metrics=schemas.MetricsInfo(
            total_return=backtest.metrics.total_return,
            sharpe=backtest.metrics.sharpe,
            max_drawdown=backtest.metrics.max_drawdown,
            win_rate=backtest.metrics.win_rate,
            avg_trade_return=backtest.metrics.avg_trade_return
        ),
        trades=[
            schemas.TradeInfo(
                date=trade.date,
                side=trade.side,
                price=trade.price,
                size=trade.size,
                commission=trade.commission,
                pnl=trade.pnl
            ) for trade in backtest.trades
        ],
        daily_positions=[
            schemas.DailyPositionInfo(
                date=pos.date,
                position_size=pos.position_size,
                cash=pos.cash,
                equity=pos.equity,
                drawdown=daily_positions[i]
            ) for i, pos in enumerate(backtest.daily_positions)
        ],
        equity_curve=[
            {"date": pos.date.isoformat(), "equity": pos.equity}
            for pos in backtest.daily_positions
        ]
    )

@router.get('/backtests', response_model=schemas.BacktestListResponse)
def list_backtests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    ticker: Optional[str] = None,
    strategy_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    backtests, total = crud.get_backtests_paginated(
        db, page, page_size, ticker, strategy_type
    )
    
    return schemas.BacktestListResponse(
        items=[
            schemas.BacktestListItem(
                id=bt.id,
                created_at=bt.created_at,
                ticker=bt.ticker,
                strategy_type=bt.strategy_type,
                start_date=bt.start_date,
                end_date=bt.end_date,
                status=bt.status
            ) for bt in backtests
        ],
        total=total,
        page=page,
        page_size=page_size
    )

@router.post('/data/indicators/update')
async def update_indicators(
    request: schemas.IndicatorUpdateRequest,
    db: Session = Depends(get_db)
):
    """Forçar atualização de indicadores para um ticker"""
    try:
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        
        df = await download_and_store_data(
            request.ticker, 
            start_date.isoformat(), 
            end_date.isoformat(), 
            db
        )
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found for ticker")
        
        return {
            "status": "success",
            "ticker": request.ticker,
            "records_updated": len(df),
            "message": f"Indicators updated for {request.ticker}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    