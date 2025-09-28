import logging
import structlog
import os

def configure_logging() -> None:
    """Configurar logging estruturado JSON"""
    
    environment = os.getenv("ENVIRONMENT", "development")
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    def add_logger_name(_, __, event_dict):
        event_dict["logger_name"] = _.name
        return event_dict
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if environment == "development":
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    """Função para obter logger estruturado"""
    return structlog.get_logger(name)

# Configurar logging automaticamente na importação
configure_logging()