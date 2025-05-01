# # Tests for execution queries

from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTransitionRequest,
    Execution,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.executions.count_executions import count_executions
from agents_api.queries.executions.count_transitions import count_transitions
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
from ward import raises, test

from tests.fixtures import (
    pg_dsn,
    test_developer_id,
    test_execution,
    test_execution_started,
    test_task,
)

MODEL = "gpt-4o-mini"


@test("query: create execution")
async def _(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
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


@test("query: get execution")
async def _(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
    pool = await create_db_pool(dsn=dsn)
    result = await get_execution(
        execution_id=execution.id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Execution)
    assert result.status == "queued"


@test("query: lookup temporal id")
async def _(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
    pool = await create_db_pool(dsn=dsn)
    result = await lookup_temporal_data(
        execution_id=execution.id,
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert result is not None
    assert result["id"]


@test("query: list executions")
async def _(
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


@test("query: list executions, invalid limit")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            limit=101,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"

    with raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            limit=0,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"


@test("query: list executions, invalid offset")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            offset=-1,
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Offset must be >= 0"


@test("query: list executions, invalid sort by")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            sort_by="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort field"


@test("query: list executions, invalid sort direction")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    """Test that listing executions with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_executions(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
            direction="invalid",
        )

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


@test("query: count executions")
async def _(
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


@test("query: create execution transition")
async def _(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
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


@test("query: create execution transition - validate transition targets")
async def _(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution):
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


@test("query: create execution transition with execution update")
async def _(
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


@test("query: get execution with transitions count")
async def _(dsn=pg_dsn, developer_id=test_developer_id, execution=test_execution_started):
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


@test("query: list executions with latest_executions view")
async def _(
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


@test("query: execution with finish transition")
async def _(
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


@test("query: execution with error transition")
async def _(
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


@test("query: count transitions by developer")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    task=test_task,
):
    pool = await create_db_pool(dsn=dsn)

    # Create a new execution for testing transitions
    execution = await create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "transition_count_test"}),
        connection_pool=pool,
    )

    # Create a workflow handle for temporal lookup
    workflow_handle = WorkflowHandle(
        client=None,
        id="transition_count_test",
    )
    await create_temporal_lookup(
        execution_id=execution.id,
        workflow_handle=workflow_handle,
        connection_pool=pool,
    )

    # Create a test transition
    scope_id = uuid7()
    await create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            type="init",
            output={"result": "initialization"},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next={"workflow": "main", "step": 0, "scope_id": scope_id},
        ),
        connection_pool=pool,
    )

    # Get transition count
    count_result = await count_transitions(
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert count_result is not None
    assert isinstance(count_result, dict)
    assert "count" in count_result
    assert isinstance(count_result["count"], int)
    assert count_result["count"] == 1
