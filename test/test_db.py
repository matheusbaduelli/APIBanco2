import pytest
from unittest.mock import patch, MagicMock

# 1. Ajuste a importação da função:
from app.db.base import create_tables,test_connection,get_engine_config

# 2. Defina o caminho do módulo para os mocks de patch:
MODULE_PATH = 'app.db.base' 

# --- Teste de Sucesso ---

@patch(f'{MODULE_PATH}.print')
@patch(f'{MODULE_PATH}.Base')
@patch(f'{MODULE_PATH}.engine')
def test_create_tables_success(mock_engine, mock_Base, mock_print):
    """
    Testa se a função cria as tabelas com sucesso e retorna True.
    """
    # Configura o mock para que create_all não levante exceção
    mock_Base.metadata.create_all.return_value = None

    # Executa a função
    result = create_tables()

    # 1. Verifica se a função retorna True
    assert result is True

    # 2. Verifica se Base.metadata.create_all foi chamado com o motor correto
    mock_Base.metadata.create_all.assert_called_once_with(bind=mock_engine)

    # 3. Verifica se a mensagem de sucesso foi impressa
    mock_print.assert_called_once_with("Tabelas criadas com sucesso!")

# --- Teste de Falha (Exceção) ---

@patch(f'{MODULE_PATH}.print')
@patch(f'{MODULE_PATH}.Base')
@patch(f'{MODULE_PATH}.engine')
def test_create_tables_failure(mock_engine, mock_Base, mock_print):
    """
    Testa se a função lida com exceções, retorna False e imprime o erro.
    """
    # Configura o mock para simular um erro no banco de dados
    mock_error = Exception("Permissão negada ao BD")
    mock_Base.metadata.create_all.side_effect = mock_error

    # Executa a função
    result = create_tables()

    # 1. Verifica se a função retorna False
    assert result is False

    # 2. Verifica se a mensagem de erro correta foi impressa
    mock_print.assert_called_with(f"Erro ao criar tabelas: {mock_error}")


@patch(f'{MODULE_PATH}.print')
@patch(f'{MODULE_PATH}.engine')
def test_db_connection_success(mock_engine, mock_print):
    """
    Testa se a conexão com o banco é estabelecida e a consulta é executada.
    Deve retornar True e não imprimir nada.
    """
    # 1. Configurar Mock da Conexão
    mock_conn = MagicMock()
    # Simula o retorno do método connect() em um bloco 'with'
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    # 2. Executa a função
    result = test_connection()

    # 3. Asserções
    assert result is True
    
    # Verifica se a função de conexão foi chamada
    mock_engine.connect.assert_called_once()
    
    # Verifica se a consulta 'SELECT 1' foi executada na conexão
    mock_conn.execute.assert_called_once_with("SELECT 1")
    
    # Verifica se nenhuma mensagem de erro foi impressa
    mock_print.assert_not_called() 

# --- Teste de Falha (Exceção) ---

@patch(f'{MODULE_PATH}.print')
@patch(f'{MODULE_PATH}.engine')
def test_db_connection_failure(mock_engine, mock_print):
    """
    Testa se a função captura uma exceção de conexão, retorna False e imprime o erro.
    """
    # 1. Configurar Mock de Falha
    mock_error = Exception("Timeout: o servidor não respondeu")
    
    # Faz com que o método connect() levante uma exceção (simulando falha de conexão)
    mock_engine.connect.side_effect = mock_error

    # 2. Executa a função
    result = test_connection()

    # 3. Asserções
    assert result is False
    
    # Verifica se o método connect foi chamado
    mock_engine.connect.assert_called_once()

    # Verifica se a mensagem de erro correta foi impressa
    mock_print.assert_called_once_with(f"Erro de conexão com banco: {mock_error}")



def setup_getenv_mock(mock_getenv, echo_val='false', pool_size='10', max_overflow='20', pool_timeout='30', pool_recycle='3600'):
    """Configura o mock de os.getenv para controlar variáveis de ambiente."""
    
    # Define uma função side_effect para mapear as chaves de ambiente para os valores de teste
    def side_effect(key, default=None):
        if key == 'SQLALCHEMY_ECHO':
            return echo_val
        elif key == 'DB_POOL_SIZE':
            return pool_size
        elif key == 'DB_MAX_OVERFLOW':
            return max_overflow
        elif key == 'DB_POOL_TIMEOUT':
            return pool_timeout
        elif key == 'DB_POOL_RECYCLE':
            return pool_recycle
        return default

    mock_getenv.side_effect = side_effect

# -------------------------- TESTES --------------------------

@patch(f'{MODULE_PATH}.QueuePool')
@patch(f'{MODULE_PATH}.os.getenv')
def test_default_config_echo_false(mock_getenv, mock_queuepool):
    """Testa a configuração padrão (não PostgreSQL nem SQLite) com ECHO=false."""
    setup_getenv_mock(mock_getenv, echo_val='false')
    db_url = "mysql://user:pass@host/db"
    
    config = get_engine_config(db_url)
    
    assert config == {
        'echo': False,
    }

@patch(f'{MODULE_PATH}.QueuePool')
@patch(f'{MODULE_PATH}.os.getenv')
def test_default_config_echo_true(mock_getenv, mock_queuepool):
    """Testa a configuração padrão com SQLALCHEMY_ECHO=true."""
    setup_getenv_mock(mock_getenv, echo_val='true')
    db_url = "oracle://user:pass@host/db"
    
    config = get_engine_config(db_url)
    
    assert config == {
        'echo': True,
    }

@patch(f'{MODULE_PATH}.QueuePool')
@patch(f'{MODULE_PATH}.os.getenv')
def test_postgresql_config_with_defaults(mock_getenv, mock_queuepool):
    """Testa a configuração para PostgreSQL usando valores padrão (defaults)."""
    setup_getenv_mock(mock_getenv, echo_val='false') 
    db_url = "postgresql://user:pass@host/db"
    
    config = get_engine_config(db_url)
    
    assert config == {
        'echo': False,
        'pool_size': 10,  # Valor padrão '10'
        'max_overflow': 20, # Valor padrão '20'
        'pool_timeout': 30, # Valor padrão '30'
        'pool_recycle': 3600, # Valor padrão '3600'
        'pool_pre_ping': True,
        'poolclass': mock_queuepool, # Deve ser o objeto mockado
    }

@patch(f'{MODULE_PATH}.QueuePool')
@patch(f'{MODULE_PATH}.os.getenv')
def test_postgresql_config_with_custom_env_vars(mock_getenv, mock_queuepool):
    """Testa a configuração para PostgreSQL usando valores customizados das variáveis de ambiente."""
    setup_getenv_mock(
        mock_getenv, 
        echo_val='true', 
        pool_size='50', 
        max_overflow='100', 
        pool_timeout='60', 
        pool_recycle='1800'
    )
    db_url = "postgresql+psycopg2://user:pass@host/db"
    
    config = get_engine_config(db_url)
    
    assert config == {
        'echo': True,
        'pool_size': 50,
        'max_overflow': 100,
        'pool_timeout': 60,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'poolclass': mock_queuepool,
    }

@patch(f'{MODULE_PATH}.os.makedirs')
@patch(f'{MODULE_PATH}.os.path') 
@patch(f'{MODULE_PATH}.os.getenv')
def test_sqlite_in_memory_config(mock_getenv, mock_path, mock_makedirs):
    """Testa a configuração para SQLite em memória ("sqlite://")."""
    setup_getenv_mock(mock_getenv, echo_val='false')
    db_url = "sqlite://"
    
    config = get_engine_config(db_url)
    
    assert config == {
        'echo': False,
        'connect_args': {"check_same_thread": False}
    }
    # Verifica se os.makedirs NÃO foi chamado
    mock_makedirs.assert_not_called()

@patch(f'{MODULE_PATH}.os.makedirs')
@patch(f'{MODULE_PATH}.os.path') # Mock os.path para simular a extração do diretório
@patch(f'{MODULE_PATH}.os.getenv')
def test_sqlite_file_config_dir_created(mock_getenv, mock_path, mock_makedirs):
    """Testa a configuração para SQLite baseado em arquivo, verificando a criação do diretório."""
    setup_getenv_mock(mock_getenv, echo_val='false')
    db_url = "sqlite:///data/sub/test.db"
    db_dir = "data/sub"
    
    # Simula o retorno de os.path.dirname para o caminho do diretório
    mock_path.dirname.return_value = db_dir
    
    config = get_engine_config(db_url)
    
    assert config == {
        'echo': False,
        'connect_args': {"check_same_thread": False}
    }
    
    # 1. Verifica se os.path.dirname foi chamado
    mock_path.dirname.assert_called_once()
    
    # 2. Verifica se os.makedirs foi chamado com o diretório e exist_ok=True
    mock_makedirs.assert_called_once_with(db_dir, exist_ok=True)