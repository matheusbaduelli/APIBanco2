import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.Api import schemas
from app.Api.routes import run_backtest_endpoint

# Mock request
mock_request = MagicMock()
mock_request.ticker = "PETR4"
mock_request.start_date = date(2023, 1, 1)
mock_request.end_date = date(2023, 12, 31)
mock_request.strategy_type = "SMA_Cross"
mock_request.strategy_params = {"fast": 20, "slow": 50}
mock_request.initial_cash = 10000.0
mock_request.commission = 0.001


@pytest.mark.asyncio
@patch("app.Api.routes.asyncio.create_task")
@patch("app.Api.routes.crud")
async def test_run_backtest_success(mock_crud, mock_create_task):
    """Testa execução bem-sucedida do endpoint de backtest"""

    mock_backtest_db_object = MagicMock(id=123)
    mock_crud.create_backtest.return_value = mock_backtest_db_object
    mock_db_session = MagicMock(spec=Session)

    response = await run_backtest_endpoint(
        request=mock_request,
        db=mock_db_session
    )

    expected_data = {
        "ticker": "PETR4",
        "start_date": mock_request.start_date,
        "end_date": mock_request.end_date,
        "strategy_type": "SMA_Cross",
        "strategy_params_json": mock_request.strategy_params,
        "initial_cash": 10000.0,
        "commission": 0.001,
        "status": "running"
    }
    mock_crud.create_backtest.assert_called_once_with(mock_db_session, expected_data)

    # Verifica se create_task foi chamado com uma coroutine
    assert mock_create_task.call_count == 1
    import types
    called_coro = mock_create_task.call_args[0][0]
    assert isinstance(called_coro, types.CoroutineType)

    # Verifica a resposta
    assert response.id == 123
    assert response.status == "running"



@pytest.mark.asyncio
@patch("app.Api.routes.crud")
@patch("app.Api.routes.asyncio.create_task")
async def test_run_backtest_failure(mock_create_task, mock_crud):
    """Testa falha do endpoint de backtest e captura HTTPException"""

    mock_db_session = MagicMock(spec=Session)
    
    # Simula falha no CRUD
    mock_crud.create_backtest.side_effect = Exception("Falha de conexão com o DB ao criar registro")

    with pytest.raises(HTTPException) as excinfo:
        await run_backtest_endpoint(
            request=mock_request,
            db=mock_db_session
        )
    
    # Verifica HTTPException
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Falha de conexão com o DB ao criar registro"

    # Verifica que a tarefa assíncrona não foi chamada
    mock_create_task.assert_not_called()
