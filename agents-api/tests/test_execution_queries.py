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
from temporalio.client import WorkflowHandle
from ward import test

from tests.fixtures import (
    pg_dsn,
    test_developer_id,
    test_execution,
    test_execution_started,
    test_task,
)
from uuid_extensions import uuid7

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
