from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.Api import routes
from app.db import base
from app.core.logging import configure_logging, get_logger

# Configurar logging no startup
configure_logging()
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    logger.info("Starting Trading Backtest API")
    
    try:
        # Criar tabelas do banco
        base.Base.metadata.create_all(bind=base.engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Trading Backtest API")

app = FastAPI(
    title="Trading Backtest API",
    description="API para backtests de estratégias de trend following",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(routes.router)