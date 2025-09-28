import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

# Importar configuração centralizada
from ..core.config import DATABASE_URL

# Configurações específicas para PostgreSQL
def get_engine_config(db_url: str):
    """Retorna configuração otimizada baseada no tipo de banco"""
    config = {
        'echo': os.getenv('SQLALCHEMY_ECHO', 'false').lower() == 'true',
    }
    
    if db_url.startswith('postgresql'):
        # Configurações específicas para PostgreSQL
        config.update({
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')), 
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),  # 1 hora
            'pool_pre_ping': True,  # Verificar conexões antes de usar
            'poolclass': QueuePool,
        })
    elif db_url.startswith('sqlite'):
        # Configurações específicas para SQLite (desenvolvimento)
        config.update({
            'connect_args': {"check_same_thread": False}
        })
        # Criar diretório para SQLite se necessário
        if ":///" in db_url:
            db_path = db_url.split("///")[1]
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
    
    return config

# Criar engine com configurações otimizadas
engine_config = get_engine_config(DATABASE_URL)
engine = create_engine(DATABASE_URL, **engine_config)

# Configurar SessionLocal
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    # Configurações adicionais para performance
    expire_on_commit=False  # Evita lazy loading depois do commit
)

# Base para modelos ORM (SQLAlchemy 2.0)
Base = declarative_base()

# Função para testar conexão
def test_connection():
    """Testa conectividade com o banco de dados"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Erro de conexão com banco: {e}")
        return False

# Função para criar todas as tabelas
def create_tables():
    """Criar todas as tabelas no banco"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
        return False