# Tests for execution queries
from uuid import uuid4

from cozo_migrate.api import apply, init
from pycozo import Client
from ward import test

from agents_api.autogen.openapi_model import Execution, Transition

from .create_execution import create_execution
from .create_execution_transition import create_execution_transition
from .get_execution import get_execution
from .get_execution_transition import get_execution_transition
from .list_execution_transitions import list_execution_transitions
from .list_executions import list_executions

MODEL = "julep-ai/samantha-1-turbo"


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create execution")
def _():
    client = cozo_client()
    developer_id = uuid4()
    task_id = uuid4()
    execution_id = uuid4()

    create_execution(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data={"input": "test"},
        client=client,
    )


@test("model: create execution with session")
def _():
    client = cozo_client()
    developer_id = uuid4()
    task_id = uuid4()
    execution_id = uuid4()
    session_id = uuid4()

    create_execution(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data={"input": "test", "session_id": session_id},
        client=client,
    )


@test("model: get execution")
def _():
    client = cozo_client()
    developer_id = uuid4()
    task_id = uuid4()
    execution_id = uuid4()

    create_execution(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data={"input": "test"},
        client=client,
    )

    result = get_execution(
        execution_id=execution_id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, Execution)
    assert result.status == "queued"


@test("model: list executions empty")
def _():
    client = cozo_client()
    developer_id = uuid4()
    task_id = uuid4()

    result = list_executions(
        developer_id=developer_id,
        task_id=task_id,
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) == 0


@test("model: list executions")
def _():
    client = cozo_client()
    developer_id = uuid4()
    task_id = uuid4()
    execution_id = uuid4()

    create_execution(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data={"input": "test"},
        client=client,
    )

    result = list_executions(
        developer_id=developer_id,
        task_id=task_id,
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].status == "queued"


@test("model: create execution transition")
def _():
    client = cozo_client()
    developer_id = uuid4()
    execution_id = uuid4()
    transition_id = uuid4()

    create_execution_transition(
        developer_id=developer_id,
        execution_id=execution_id,
        transition_id=transition_id,
        data={
            "type": "step",
            "from": "test",
            "to": "test",
            "outputs": {"input": "test"},
        },
        client=client,
    )


@test("model: get execution transition")
def _():
    client = cozo_client()
    developer_id = uuid4()
    execution_id = uuid4()
    transition_id = uuid4()

    create_execution_transition(
        developer_id=developer_id,
        execution_id=execution_id,
        transition_id=transition_id,
        data={
            "type": "step",
            "from": "test",
            "to": "test",
            "outputs": {"input": "test"},
        },
        client=client,
    )

    result = get_execution_transition(
        developer_id=developer_id,
        transition_id=transition_id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, Transition)
    assert result.type == "step"


@test("model: list execution transitions")
def _():
    client = cozo_client()
    developer_id = uuid4()
    execution_id = uuid4()
    transition_id = uuid4()

    create_execution_transition(
        developer_id=developer_id,
        execution_id=execution_id,
        transition_id=transition_id,
        data={
            "type": "step",
            "from": "test",
            "to": "test",
            "outputs": {"input": "test"},
        },
        client=client,
    )

    result = list_execution_transitions(
        developer_id=developer_id,
        execution_id=execution_id,
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == "step"
