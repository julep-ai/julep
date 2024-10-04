# Tests for task queries
from uuid import uuid4

from ward import test

from agents_api.autogen.openapi_model import (
    CreateTaskRequest,
    ResourceUpdatedResponse,
    Task,
    UpdateTaskRequest,
)
from agents_api.models.task.create_or_update_task import create_or_update_task
from agents_api.models.task.create_task import create_task
from agents_api.models.task.delete_task import delete_task
from agents_api.models.task.get_task import get_task
from agents_api.models.task.list_tasks import list_tasks
from agents_api.models.task.update_task import update_task

from tests.fixtures import cozo_client, test_agent, test_developer_id, test_task


@test("model: create task")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    task_id = uuid4()

    create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=task_id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [{"evaluate": {"hi": "_"}}],
            }
        ),
        client=client,
    )


@test("model: create or update task")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    task_id = uuid4()

    create_or_update_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=task_id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [{"evaluate": {"hi": "_"}}],
            }
        ),
        client=client,
    )


@test("model: get task not exists")
def _(client=cozo_client, developer_id=test_developer_id):
    task_id = uuid4()

    try:
        get_task(
            developer_id=developer_id,
            task_id=task_id,
            client=client,
        )
    except Exception:
        pass
    else:
        assert False, "Task should not exist"


@test("model: get task exists")
def _(client=cozo_client, developer_id=test_developer_id, task=test_task):
    result = get_task(
        developer_id=developer_id,
        task_id=task.id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, Task)


@test("model: delete task")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    task = create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            **{
                "name": "test task",
                "description": "test task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [{"evaluate": {"hi": "_"}}],
            }
        ),
        client=client,
    )

    delete_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=task.id,
        client=client,
    )

    try:
        get_task(
            developer_id=developer_id,
            task_id=task.id,
            client=client,
        )
    except Exception:
        pass

    else:
        assert False, "Task should not exist"


@test("model: update task")
def _(
    client=cozo_client, developer_id=test_developer_id, agent=test_agent, task=test_task
):
    result = update_task(
        developer_id=developer_id,
        task_id=task.id,
        agent_id=agent.id,
        data=UpdateTaskRequest(
            **{
                "name": "updated task",
                "description": "updated task about",
                "input_schema": {"type": "object", "additionalProperties": True},
                "main": [{"evaluate": {"hi": "_"}}],
            }
        ),
        client=client,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)


@test("model: list tasks")
def _(
    client=cozo_client, developer_id=test_developer_id, task=test_task, agent=test_agent
):
    result = list_tasks(
        developer_id=developer_id,
        agent_id=agent.id,
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(task, Task) for task in result)
