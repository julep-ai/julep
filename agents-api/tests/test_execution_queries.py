# Tests for execution queries

from temporalio.client import WorkflowHandle
from ward import test

from agents_api.autogen.Executions import (
    CreateExecutionRequest,
)
from agents_api.autogen.openapi_model import CreateTransitionRequest, Execution
from agents_api.models.execution.create_execution import create_execution
from agents_api.models.execution.create_execution_transition import (
    create_execution_transition,
)
from agents_api.models.execution.get_execution import get_execution
from agents_api.models.execution.list_executions import list_executions
from tests.fixtures import cozo_client, test_developer_id, test_execution, test_task

MODEL = "gpt-4o"


@test("model: create execution")
def _(client=cozo_client, developer_id=test_developer_id, task=test_task):
    workflow_handle = WorkflowHandle(
        client=None,
        id="blah",
    )

    create_execution(
        developer_id=developer_id,
        task_id=task.id,
        data=CreateExecutionRequest(input={"test": "test"}),
        workflow_handle=workflow_handle,
        client=client,
    )


@test("model: get execution")
def _(client=cozo_client, developer_id=test_developer_id, execution=test_execution):
    result = get_execution(
        execution_id=execution.id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, Execution)
    assert result.status == "queued"


@test("model: list executions")
def _(
    client=cozo_client,
    developer_id=test_developer_id,
    execution=test_execution,
    task=test_task,
):
    result = list_executions(
        developer_id=developer_id,
        task_id=task.id,
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].status == "queued"


@test("model: create execution transition")
def _(client=cozo_client, developer_id=test_developer_id, execution=test_execution):
    result = create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            **{
                "type": "step",
                "output": {"result": "test"},
                "current": ["main", 0],
                "next": None,
            }
        ),
        client=client,
    )

    assert result is not None
    assert result.type == "step"
    assert result.output == {"result": "test"}


@test("model: create execution transition with execution update")
def _(
    client=cozo_client,
    developer_id=test_developer_id,
    task=test_task,
    execution=test_execution,
):
    result = create_execution_transition(
        developer_id=developer_id,
        execution_id=execution.id,
        data=CreateTransitionRequest(
            **{
                "type": "step",
                "output": {"result": "test"},
                "current": ["main", 0],
                "next": None,
            }
        ),
        task_id=task.id,
        update_execution_status=True,
        client=client,
    )

    assert result is not None
    assert result.type == "step"
    assert result.output == {"result": "test"}
