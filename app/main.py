from fastapi import FastAPI
from app.Api import routes
from db import session, base, models
from core.logging import configure_logging, get_logger
import os

# Configurar logging no startup
configure_logging()
logger = get_logger("main")

app = FastAPI(
    title="Trading Backtest API",
    description="API para backtests de estratégias de trend following",
    version="1.0.0"
)

app.include_router(routes.router)

@app.on_event("startup")
def startup():
    """Inicializar aplicação"""
    logger.info("Starting Trading Backtest API")
    
    try:
        # Criar tabelas do banco
        base.Base.metadata.create_all(bind=session.engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

@app.on_event("shutdown") 
def shutdown():
    """Finalizar aplicação"""
    logger.info("Shutting down Trading Backtest API")