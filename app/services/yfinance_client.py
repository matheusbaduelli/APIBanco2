import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from ..db import models, crud
import logging
from sqlalchemy import and_

logger = logging.getLogger(__name__)

async def download_and_store_data(ticker: str, start_date: str, end_date: str, db: Session) -> pd.DataFrame:
    """Download de dados do Yahoo Finance e armazenamento no banco"""
    try:
        
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if df.empty:
            logger.warning(f"No data found for {ticker}")
            return None
        
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Missing column {col} for {ticker}")
                return None
        
        
        symbol = db.query(models.Symbol).filter(models.Symbol.ticker == ticker).first()
        if not symbol:
            symbol = models.Symbol(
                ticker=ticker,
                name=ticker,  
                exchange="UNKNOWN",
                currency="USD"
            )
            db.add(symbol)
            db.commit()
            db.refresh(symbol)
        
        
        for date, row in df.iterrows():
            
            existing = db.query(models.Price).filter(
                and_(models.Price.symbol_id == symbol.id, 
                     models.Price.date == date.date())
            ).first()
            
            if not existing:
                price = models.Price(
                    symbol_id=symbol.id,
                    date=date.date(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else 0
                )
                db.add(price)
        
        db.commit()
        
        
        await calculate_and_store_indicators(symbol.id, df, db)
        
        logger.info(f"Successfully stored data for {ticker}: {len(df)} records")
        return df
        
    except Exception as e:
        logger.error(f"Error downloading/storing data for {ticker}: {str(e)}")
        raise e

async def calculate_and_store_indicators(symbol_id: int, df: pd.DataFrame, db: Session):
    """Calcular e armazenar indicadores técnicos"""
    try:
       
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        
        df['TR'] = df[['High', 'Low', 'Close']].apply(
            lambda x: max(x['High'] - x['Low'], 
                         abs(x['High'] - x['Close']), 
                         abs(x['Low'] - x['Close'])), axis=1)
        df['ATR_14'] = df['TR'].rolling(window=14).mean()
        
        
        df['ROC_60'] = df['Close'].pct_change(periods=60)
        
        
        indicators_to_store = [
            ('SMA', df['SMA_20'], '{"period": 20}'),
            ('SMA', df['SMA_50'], '{"period": 50}'),
            ('SMA', df['SMA_200'], '{"period": 200}'),
            ('ATR', df['ATR_14'], '{"period": 14}'),
            ('ROC', df['ROC_60'], '{"period": 60}')
        ]
        
        for name, series, params_hash in indicators_to_store:
            for date, value in series.dropna().items():
                existing = db.query(models.Indicator).filter(
                    and_(
                        models.Indicator.symbol_id == symbol_id,
                        models.Indicator.date == date.date(),
                        models.Indicator.name == name,
                        models.Indicator.params_hash == params_hash
                    )
                ).first()
                
                if not existing:
                    indicator = models.Indicator(
                        symbol_id=symbol_id,
                        date=date.date(),
                        name=name,
                        value=float(value),
                        params_hash=params_hash
                    )
                    db.add(indicator)
        
        db.commit()
        logger.info(f"Indicators calculated and stored for symbol_id {symbol_id}")
        
    except Exception as e:
        logger.error(f"Error calculating indicators for symbol_id {symbol_id}: {str(e)}")
        raise e