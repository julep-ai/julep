# # Tests for execution queries

import pytest
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

MODEL = "gpt-4o-mini"


async def test_query_create_execution(pg_dsn, test_developer_id, test_task):
    pool = await create_db_pool(dsn=pg_dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    execution = await create_execution(
        developer_id=test_developer_id,
        task_id=test_task.id,
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


async def test_query_get_execution(pg_dsn, test_developer_id, test_execution):
    pool = await create_db_pool(dsn=pg_dsn)
    result = await get_execution(
        execution_id=test_execution.id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Execution)
    assert result.status == "queued"


async def test_query_lookup_temporal_id(pg_dsn, test_developer_id, test_execution):
    pool = await create_db_pool(dsn=pg_dsn)
    result = await lookup_temporal_data(
        execution_id=test_execution.id,
        developer_id=test_developer_id,
        connection_pool=pool,
    )

    assert result is not None
    assert result["id"]


async def test_query_list_executions(
    pg_dsn,
    test_developer_id,
    test_execution_started,
    test_task,
):
    pool = await create_db_pool(dsn=pg_dsn)
    result = await list_executions(
        developer_id=test_developer_id,
        task_id=test_task.id,
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].status == "starting"


async def test_query_list_executions_invalid_limit(
    pg_dsn,
    test_developer_id,
    test_task,
):
    """Test that listing executions with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=test_developer_id,
            task_id=test_task.id,
            connection_pool=pool,
            limit=101,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"

    with pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=test_developer_id,
            task_id=test_task.id,
            connection_pool=pool,
            limit=0,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"


async def test_query_list_executions_invalid_offset(
    pg_dsn,
    test_developer_id,
    test_task,
):
    """Test that listing executions with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=test_developer_id,
            task_id=test_task.id,
            connection_pool=pool,
            offset=-1,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Offset must be >= 0"


async def test_query_list_executions_invalid_sort_by(
    pg_dsn,
    test_developer_id,
    test_task,
):
    """Test that listing executions with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=test_developer_id,
            task_id=test_task.id,
            connection_pool=pool,
            sort_by="invalid",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort field"


async def test_query_list_executions_invalid_sort_direction(
    pg_dsn,
    test_developer_id,
    test_task,
):
    """Test that listing executions with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_executions(
            developer_id=test_developer_id,
            task_id=test_task.id,
            connection_pool=pool,
            direction="invalid",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort direction"


async def test_query_count_executions(
    pg_dsn,
    test_developer_id,
    test_execution_started,
    test_task,
):
    pool = await create_db_pool(dsn=pg_dsn)
    result = await count_executions(
        developer_id=test_developer_id,
        task_id=test_task.id,
        connection_pool=pool,
    )

    assert isinstance(result, dict)
    assert result["count"] > 0


async def test_query_create_execution_transition(
    pg_dsn, test_developer_id, test_execution
):
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = uuid7()
    result = await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution.id,
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


async def test_query_create_execution_transition_validate_transition_targets(
    pg_dsn, test_developer_id, test_execution
):
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = uuid7()
    await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution.id,
        data=CreateTransitionRequest(
            type="init_branch",
            output={"result": "test"},
            current={"workflow": "subworkflow", "step": 0, "scope_id": scope_id},
            next={"workflow": "subworkflow", "step": 0, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution.id,
        data=CreateTransitionRequest(
            type="step",
            output={"result": "test"},
            current={"workflow": "subworkflow", "step": 0, "scope_id": scope_id},
            next={"workflow": "subworkflow", "step": 1, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    result = await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution.id,
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


async def test_query_create_execution_transition_with_execution_update(
    pg_dsn,
    test_developer_id,
    test_execution_started,
):
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = uuid7()
    result = await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution_started.id,
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


async def test_query_get_execution_with_transitions_count(
    pg_dsn, test_developer_id, test_execution_started
):
    pool = await create_db_pool(dsn=pg_dsn)
    result = await get_execution(
        execution_id=test_execution_started.id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Execution)
    assert result.status == "starting"
    # Since we create one init transition in the test_execution_started fixture
    assert result.transition_count == 1


async def test_query_list_executions_with_latest_executions_view(
    pg_dsn,
    test_developer_id,
    test_execution_started,
    test_task,
):
    pool = await create_db_pool(dsn=pg_dsn)
    result = await list_executions(
        developer_id=test_developer_id,
        task_id=test_task.id,
        sort_by="updated_at",
        direction="asc",
        connection_pool=pool,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].status == "starting"
    # Since we create one init transition in the test_execution_started fixture
    assert hasattr(result[0], "transition_count")


async def test_query_execution_with_finish_transition(
    pg_dsn,
    test_developer_id,
    test_execution_started,
):
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = uuid7()

    # Create a finish transition - this would have failed with the old query
    # because there's no step definition for finish transitions
    await create_execution_transition(
        developer_id=test_developer_id,
        execution_id=test_execution_started.id,
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
        execution_id=test_execution_started.id,
        connection_pool=pool,
    )

    assert result is not None
    assert result.status == "succeeded"
    assert result.transition_count == 2  # init + finish


async def test_query_execution_with_error_transition(
    pg_dsn,
    test_developer_id,
    test_task,
):
    pool = await create_db_pool(dsn=pg_dsn)
    workflow_handle = WorkflowHandle(
        client=None,
        id="error_test",
    )

    # Create a new execution
    execution = await create_execution(
        developer_id=test_developer_id,
        task_id=test_task.id,
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
        developer_id=test_developer_id,
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
        developer_id=test_developer_id,
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
