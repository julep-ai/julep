# Tests for task queries
from uuid import uuid4

from cozo_migrate.api import apply, init
from pycozo import Client
from ward import test

from agents_api.autogen.openapi_model import Task
from agents_api.models.task.create_task import create_task
from agents_api.models.task.delete_task import delete_task
from agents_api.models.task.get_task import get_task
from agents_api.models.task.list_tasks import list_tasks
from agents_api.models.task.update_task import update_task


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create task")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()
    task_id = uuid4()

    create_task(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        data={
            "name": "test task",
            "description": "test task about",
            "input_schema": {"type": "object", "additionalProperties": True},
        },
        client=client,
    )


@test("model: get task not exists")
def _():
    client = cozo_client()
    developer_id = uuid4()
    task_id = uuid4()

    try:
        get_task(
            developer_id=developer_id,
            task_id=task_id,
            client=client,
        )
    except Exception as e:
        assert str(e) == "Task not found"


@test("model: get task exists")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()
    task_id = uuid4()

    create_task(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        data={
            "name": "test task",
            "description": "test task about",
            "input_schema": {"type": "object", "additionalProperties": True},
        },
        client=client,
    )

    result = get_task(
        developer_id=developer_id,
        task_id=task_id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, Task)


@test("model: delete task")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()
    task_id = uuid4()

    create_task(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        data={
            "name": "test task",
            "description": "test task about",
            "input_schema": {"type": "object", "additionalProperties": True},
        },
        client=client,
    )

    delete_task(
        developer_id=developer_id,
        task_id=task_id,
        client=client,
    )

    try:
        get_task(
            developer_id=developer_id,
            task_id=task_id,
            client=client,
        )
    except Exception as e:
        assert str(e) == "Task not found"


@test("model: update task")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()
    task_id = uuid4()

    create_task(
        developer_id=developer_id,
        agent_id=agent_id,
        task_id=task_id,
        data={
            "name": "test task",
            "description": "test task about",
            "input_schema": {"type": "object", "additionalProperties": True},
        },
        client=client,
    )

    result = update_task(
        developer_id=developer_id,
        task_id=task_id,
        data={
            "name": "updated task",
            "description": "updated task about",
            "input_schema": {"type": "object", "additionalProperties": True},
        },
        client=client,
    )

    assert result is not None
    assert isinstance(result, Task)
    assert result.name == "updated task"


@test("model: list tasks")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()

    result = list_tasks(
        developer_id=developer_id,
        agent_id=agent_id,
        client=client,
    )

    assert isinstance(result, list)
    assert all(isinstance(task, Task) for task in result)
