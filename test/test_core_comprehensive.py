

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from unittest.mock import Mock, patch
import os

from app.core.backtest_engine import run_backtest, PandasData, STRATEGY_MAP
from app.core.strategies.base import BaseStrategy
from app.core import config, logging


class TestBacktestEngine:
    """Testes abrangentes para o engine de backtest"""
    
    @pytest.fixture
    def sample_data(self):
        """Dados de exemplo para testes"""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        np.random.seed(42)
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 100)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        return pd.DataFrame({
            'Open': prices,
            'High': [p * 1.01 for p in prices],
            'Low': [p * 0.99 for p in prices],
            'Close': prices,
            'Volume': [1000] * 100
        }, index=dates)
    
    def test_strategy_map_completeness(self):
        """Testa se todas as estratégias estão no mapa"""
        expected_strategies = ['sma_cross', 'donchian_breakout', 'momentum']
        assert set(STRATEGY_MAP.keys()) == set(expected_strategies)
        
        for strategy_name, strategy_class in STRATEGY_MAP.items():
            assert issubclass(strategy_class, BaseStrategy)
    
    def test_run_backtest_invalid_strategy(self, sample_data):
        """Testa erro com estratégia inválida"""
        with pytest.raises(ValueError, match="Unknown strategy type"):
            run_backtest(
                sample_data, 
                'invalid_strategy', 
                {}, 
                10000.0, 
                0.001
            )
    
    def test_run_backtest_empty_dataframe(self):
        """Testa erro com DataFrame vazio"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="DataFrame is empty"):
            run_backtest(empty_df, 'sma_cross', {}, 10000.0, 0.001)
    
    def test_run_backtest_missing_columns(self):
        """Testa erro com colunas faltando"""
        incomplete_df = pd.DataFrame({
            'Open': [100, 101],
            'Close': [99, 102]
            # Missing High, Low, Volume
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            run_backtest(incomplete_df, 'sma_cross', {}, 10000.0, 0.001)
    
    def test_run_backtest_return_structure(self, sample_data):
        """Testa estrutura do retorno"""
        results = run_backtest(
            sample_data, 
            'sma_cross', 
            {'fast': 5, 'slow': 20}, 
            10000.0, 
            0.001
        )
        
        required_keys = [
            'final_cash', 'total_return', 'sharpe', 'max_drawdown',
            'trades', 'daily_positions', 'win_rate', 'avg_trade_return'
        ]
        
        for key in required_keys:
            assert key in results, f"Missing key: {key}"
        
        assert isinstance(results['final_cash'], (int, float))
        assert isinstance(results['total_return'], (int, float))
        assert isinstance(results['trades'], list)
        assert isinstance(results['daily_positions'], list)
    
    def test_pandas_data_feed(self, sample_data):
        """Testa o feed de dados personalizado"""
        data_feed = PandasData(dataname=sample_data)
        
        # Verificar parâmetros
        assert data_feed.params.open == 'Open'
        assert data_feed.params.high == 'High'
        assert data_feed.params.low == 'Low'
        assert data_feed.params.close == 'Close'
        assert data_feed.params.volume == 'Volume'


class TestBaseStrategy:
    """Testes para a classe base de estratégias"""
    
    def test_abstract_implementation(self):
        """Testa que BaseStrategy não pode ser instanciada diretamente"""
        with pytest.raises(TypeError):
            BaseStrategy()
    
    def test_position_size_calculation(self):
        """Testa cálculo de tamanho de posição"""
        # Mock de uma estratégia concreta para testar BaseStrategy
        class TestStrategy(BaseStrategy):
            def strategy_logic(self):
                pass
        
        # Mock do broker
        strategy = TestStrategy()
        strategy.broker = Mock()
        strategy.broker.get_value.return_value = 100000.0  # 100k capital
        strategy.broker.get_cash.return_value = 50000.0    # 50k disponível
        
        # Teste: preço atual 100, stop 95 (risco 5 por ação)
        # Risco 1% = 1000, então 1000/5 = 200 ações
        # Mas cash só permite 50000/100 = 500 ações
        # Deve retornar min(200, 500) = 200
        current_price = 100.0
        stop_price = 95.0
        
        size = strategy.calculate_position_size(current_price, stop_price)
        assert size == 200
    
    def test_position_size_zero_risk(self):
        """Testa posição quando risco é zero"""
        class TestStrategy(BaseStrategy):
            def strategy_logic(self):
                pass
        
        strategy = TestStrategy()
        strategy.broker = Mock()
        strategy.broker.get_value.return_value = 100000.0
        
        # Sem risco (preço = stop)
        size = strategy.calculate_position_size(100.0, 100.0)
        assert size == 0
    
    def test_trades_list_initialization(self):
        """Testa inicialização da lista de trades"""
        class TestStrategy(BaseStrategy):
            def strategy_logic(self):
                pass
        
        strategy = TestStrategy()
        assert isinstance(strategy.trades_list, list)
        assert len(strategy.trades_list) == 0
        assert isinstance(strategy.daily_positions, list)
        assert len(strategy.daily_positions) == 0


class TestStrategyLogic:
    """Testes específicos da lógica de cada estratégia"""
    
    @pytest.fixture
    def trending_data(self):
        """Dados com tendência clara para testar sinais"""
        dates = pd.date_range('2020-01-01', periods=60, freq='D')
        # Tendência ascendente clara
        prices = list(range(100, 160))
        
        return pd.DataFrame({
            'Open': prices,
            'High': [p * 1.01 for p in prices],
            'Low': [p * 0.99 for p in prices],
            'Close': prices,
            'Volume': [1000] * 60
        }, index=dates)
    
    def test_sma_cross_signals(self, trending_data):
        """Testa sinais da estratégia SMA Cross"""
        results = run_backtest(
            trending_data,
            'sma_cross',
            {'fast': 5, 'slow': 15},  # Períodos menores para dados limitados
            10000.0,
            0.001
        )
        
        # Com tendência ascendente, deve haver pelo menos 1 trade
        assert len(results['trades']) >= 1
        # Primeiro trade deve ser compra
        if results['trades']:
            assert results['trades'][0]['side'] == 'BUY'
    
    def test_donchian_breakout_signals(self, trending_data):
        """Testa sinais da estratégia Donchian"""
        results = run_backtest(
            trending_data,
            'donchian_breakout',
            {'entry_period': 10, 'exit_period': 5},
            20000.0,
            0.001
        )
        
        # Com breakout ascendente, deve haver trades
        assert len(results['trades']) >= 1
    
    def test_momentum_signals(self):
        """Testa sinais da estratégia Momentum"""
        # Dados com momentum específico
        dates = pd.date_range('2020-01-01', periods=120, freq='D')
        base = 100
        # Criar momentum: lateral por 60 dias, depois tendência
        prices = [base] * 60 + [base + i * 0.5 for i in range(1, 61)]
        
        df = pd.DataFrame({
            'Open': prices,
            'High': [p * 1.01 for p in prices],
            'Low': [p * 0.99 for p in prices],
            'Close': prices,
            'Volume': [1000] * 120
        }, index=dates)
        
        results = run_backtest(
            df,
            'momentum',
            {'lookback': 60, 'percentile_threshold': 60},
            15000.0,
            0.001
        )
        
        # Estratégia deve funcionar sem erros
        assert 'final_cash' in results
        assert isinstance(results['win_rate'], (int, float))


class TestConfigModule:
    """Testes para o módulo de configuração"""
    
    def test_default_values(self):
        """Testa valores padrão de configuração"""
        # Teste sem variáveis de ambiente
        with patch.dict(os.environ, {}, clear=True):
            # Reimportar para pegar novos valores
            import importlib
            importlib.reload(config)
            
            assert config.LOG_LEVEL == "INFO"
            assert config.ENVIRONMENT == "development"
    
    @patch.dict(os.environ, {
        'LOG_LEVEL': 'DEBUG',
        'ENVIRONMENT': 'production'
    })
    def test_environment_override(self):
        """Testa override por variáveis de ambiente"""
        import importlib
        importlib.reload(config)
        
        assert config.LOG_LEVEL == "DEBUG"
        assert config.ENVIRONMENT == "production"


class TestLoggingModule:
    """Testes para o módulo de logging"""
    
    def test_get_logger(self):
        """Testa criação de logger"""
        logger = logging.get_logger("test")
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'development'})
    def test_configure_logging_dev(self):
        """Testa configuração de logging para desenvolvimento"""
        # Deve executar sem erros
        logging.configure_logging()
        logger = logging.get_logger("test_dev")
        assert logger is not None
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_configure_logging_prod(self):
        """Testa configuração de logging para produção"""
        logging.configure_logging()
        logger = logging.get_logger("test_prod")
        assert logger is not None


class TestEdgeCases:
    """Testes de casos extremos e edge cases"""
    @pytest.fixture
    def sample_data():
        return sample_market_data()  # procurar

    
    def test_very_short_period(self):
        """Testa backtest com período muito curto"""
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        prices = list(range(100, 110))
        
        df = pd.DataFrame({
            'Open': prices,
            'High': [p * 1.01 for p in prices],
            'Low': [p * 0.99 for p in prices],
            'Close': prices,
            'Volume': [100] * 10
        }, index=dates)
        
        # Deve executar sem erro, mas pode não gerar trades
        results = run_backtest(df, 'sma_cross', {'fast': 2, 'slow': 5}, 1000.0, 0.001)
        assert 'final_cash' in results
    
    def test_high_commission(self, sample_data):
        """Testa com comissão alta"""
        results = run_backtest(
            sample_data.head(20),  # Dados reduzidos
            'sma_cross',
            {'fast': 3, 'slow': 8},
            5000.0,
            0.05  # 5% de comissão!
        )
        
        # Deve executar, provavelmente com resultado negativo
        assert results['final_cash'] >= 0  # Não pode ficar negativo
    
    def test_zero_initial_cash(self, sample_data):
        """Testa erro com capital inicial zero"""
        # Isso deve ser validado na API, mas testamos aqui também
        with pytest.raises((ValueError, Exception)):
            run_backtest(sample_data, 'sma_cross', {}, 0.0, 0.001)


# Fixture global para pytest
@pytest.fixture(scope="session")
def sample_market_data():
    """Dados de mercado reutilizáveis para todos os testes"""
    np.random.seed(123)
    dates = pd.date_range('2020-01-01', periods=200, freq='D')
    
    # Simular preços realísticos com volatilidade
    base_price = 100
    returns = np.random.normal(0.0005, 0.02, 200)  # ~13% vol anual
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(max(prices[-1] * (1 + ret), 0.01))  # Evitar preços negativos
    
    return pd.DataFrame({
        'Open': [p * 0.999 for p in prices],
        'High': [p * 1.015 for p in prices],
        'Low': [p * 0.985 for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 200)
    }, index=dates)