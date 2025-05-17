# # Tests for execution queries

from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTransitionRequest,
    Execution,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.executions.count_executions import count_executions
from agents_api.queries.executions.create_execution import create_execution
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
from agents_api.queries.executions.create_temporal_lookup import create_temporal_lookup
from agents_api.queries.executions.get_execution import get_execution
from agents_api.queries.executions.list_executions import list_executions
from agents_api.queries.executions.lookup_temporal_data import lookup_temporal_data
from fastapi import HTTPException
from temporalio.client import WorkflowHandle
from uuid_extensions import uuid7
import pytest

from tests.fixtures import (
    pg_dsn,
    test_developer_id,
    test_execution,
    test_execution_started,
    test_task,
)

MODEL = "gpt-4o-mini"


@pytest.mark.asyncio
async def test_query_create_execution(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
    """query: create execution"""
    pool = await create_db_pool(dsn=dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        connection_pool=pool,
    )

    await create_temporal_lookup(
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        connection_pool=pool,
    )

    assert execution.status == "queued"
    assert execution.input == {"test": "test"}


@pytest.mark.asyncio
async def test_query_get_execution(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
    """query: get execution"""
    pool = await create_db_pool(dsn=dsn)
    result = await get_execution(
        execution_id=execution.id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Execution)
    assert result.status == "queued"


@pytest.mark.asyncio
async def test_query_lookup_temporal_id(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
    """query: lookup temporal id"""
    pool = await create_db_pool(dsn=dsn)
    result = await lookup_temporal_data(
        execution_id=execution.id,
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert result is not None
    assert result["id"]


@pytest.mark.asyncio
async def test_query_list_executions(
    """query: list executions"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    execution=test_execution_started,
    task=test_task,
):
    pool = await create_db_pool(dsn=dsn)
    result = await list_executions(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].status == "starting"


@pytest.mark.asyncio
async def test_query_list_executions_invalid_limit(
    """query: list executions, invalid limit"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            limit=101,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"

    with pytest.pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            limit=0,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"


@pytest.mark.asyncio
async def test_query_list_executions_invalid_offset(
    """query: list executions, invalid offset"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            offset=-1,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Offset must be >= 0"


@pytest.mark.asyncio
async def test_query_list_executions_invalid_sort_by(
    """query: list executions, invalid sort by"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            sort_by="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort field"


@pytest.mark.asyncio
async def test_query_list_executions_invalid_sort_direction(
    """query: list executions, invalid sort direction"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            direction="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


@pytest.mark.asyncio
async def test_query_count_executions(
    """query: count executions"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    execution=test_execution_started,
    task=test_task,
):
    pool = await create_db_pool(dsn=dsn)
    result = await count_executions(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )

    assert isinstance(result, dict)
    assert result["count"] > 0


@pytest.mark.asyncio
async def test_query_create_execution_transition(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
    """query: create execution transition"""
    pool = await create_db_pool(dsn=dsn)
    scope_id = uuid7()
    result = await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="init_branch",
            output={"result": "test"},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next={"workflow": "main", "step": 0, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    assert result is not None
    assert result.type == "init_branch"
    assert result.output == {"result": "test"}


@pytest.mark.asyncio
async def test_query_create_execution_transition_validate_transition_targets(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
    """query: create execution transition - validate transition targets"""
    pool = await create_db_pool(dsn=dsn)
    scope_id = uuid7()
    await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="init_branch",
            output={"result": "test"},
            current={"workflow": "subworkflow", "step": 0, "scope_id": scope_id},
            next={"workflow": "subworkflow", "step": 0, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="step",
            output={"result": "test"},
            current={"workflow": "subworkflow", "step": 0, "scope_id": scope_id},
            next={"workflow": "subworkflow", "step": 1, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    result = await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="step",
            output={"result": "test"},
            current={"workflow": "subworkflow", "step": 1, "scope_id": scope_id},
            next={"workflow": "subworkflow", "step": 0, "scope_id": uuid7()},
        ),
        connection_pool=pool,
    )

    assert result is not None
    assert result.type == "step"
    assert result.output == {"result": "test"}


@pytest.mark.asyncio
async def test_query_create_execution_transition_with_execution_update(
    """query: create execution transition with execution update"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    execution=test_execution_started,
):
    pool = await create_db_pool(dsn=dsn)
    scope_id = uuid7()
    result = await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="cancelled",
            output={"result": "test"},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next=None,
        ),
        # task_id=task.id,
        # update_execution_status=True,
        connection_pool=pool,
    )

    assert result is not None
    assert result.type == "cancelled"
    assert result.output == {"result": "test"}


@pytest.mark.asyncio
async def test_query_get_execution_with_transitions_count(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution_started):
    """query: get execution with transitions count"""
    pool = await create_db_pool(dsn=dsn)
    result = await get_execution(
        execution_id=execution.id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Execution)
    assert result.status == "starting"
    # Since we create one init transition in the test_execution_started fixture
    assert result.transition_count == 1


@pytest.mark.asyncio
async def test_query_list_executions_with_latest_executions_view(
    """query: list executions with latest_executions view"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    execution=test_execution_started,
    task=test_task,
):
    pool = await create_db_pool(dsn=dsn)
    result = await list_executions(
        developer_id=developer_id,
        task_id=task.id,
        sort_by="updated_at",
        direction="asc",
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].status == "starting"
    # Since we create one init transition in the test_execution_started fixture
    assert hasattr(result[0], "transition_count")


@pytest.mark.asyncio
async def test_query_execution_with_finish_transition(
    """query: execution with finish transition"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    execution=test_execution_started,
):
    pool = await create_db_pool(dsn=dsn)
    scope_id = uuid7()

    # Create a finish transition - this would have failed with the old query
    # because there's no step definition for finish transitions
    await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="finish",
            output={"result": "completed successfully"},
            current={"workflow": "main", "step": 1, "scope_id": scope_id},
            next=None,
        ),
        connection_pool=pool,
    )

    # Get the execution and verify it has the correct status
    result = await get_execution(
        execution_id=execution.id,
        connection_pool=pool,
    )

    assert result is not None
    assert result.status == "succeeded"
    assert result.transition_count == 2  # init + finish


@pytest.mark.asyncio
async def test_query_execution_with_error_transition(
    """query: execution with error transition"""
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    pool = await create_db_pool(dsn=dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="error_test",
    )

    # Create a new execution
    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "error_test"}),
        connection_pool=pool,
    )
    await create_temporal_lookup(
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        connection_pool=pool,
    )

    scope_id = uuid7()

    # Add an init transition
    await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="init",
            output={},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next={"workflow": "main", "step": 0, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    # Add an error transition - this would have failed with the old query
    # because there's no step definition for error transitions
    await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="error",
            output={"error": "Something went wrong"},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next=None,
        ),
        connection_pool=pool,
    )

    # Get the execution and verify it has the correct status
    result = await get_execution(
        execution_id=execution.id,
        connection_pool=pool,
    )

    assert result is not None
    assert result.status == "failed"
    assert result.error == "Something went wrong"
    assert result.transition_count == 2  # init + error
