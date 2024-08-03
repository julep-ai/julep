from ward import test
from uuid import uuid4
from typing import List

from julep.api.types import (
    Task,
    Execution,
)

from .fixtures import (
    client,
    async_client,
    test_task,
    test_task_async,
    mock_task,
)


@test("tasks: tasks.create")
def _(task=test_task):
    assert isinstance(task, Task)
    assert hasattr(task, "created_at")

    assert task.name == mock_task["name"]
    assert task.description == mock_task["description"]
    assert task.tools_available == mock_task["tools_available"]
    assert task.input_schema == mock_task["input_schema"]
    assert task.main == mock_task["main"]
    assert task.agent_id == mock_task["agent_id"]


@test("tasks: tasks.get")
def _(client=client, task=test_task):
    response = client.tasks.get(task.id)
    assert isinstance(response, Task)

    assert task.name == response.name
    assert task.description == response.description
    assert task.tools_available == response.tools_available
    assert task.input_schema == response.input_schema
    assert task.main == response.main
    assert task.agent_id == response.agent_id


@test("tasks: tasks.list")
def _(client=client, _=test_task):
    response = client.tasks.list()
    assert len(response) > 0
    assert isinstance(response[0], Task)


@test("tasks: tasks.start_task_execution")
def _(client=client, _=test_task):
    response = client.tasks.start_task_execution(
        agent_id=uuid4(),
        task_id=uuid4(),
        arguments={},
        status="enqueued",
    )
    assert isinstance(response[0], Execution)


@test("tasks: tasks.get_task_execution")
def _(client=client, _=test_task):
    response = client.tasks.get_task_execution(
        task_id=uuid4(),
        execution_id=uuid4(),
    )
    assert isinstance(response[0], List[Execution])


@test("async tasks: tasks.create")
async def _(task=test_task_async):
    assert isinstance(task, Task)
    assert hasattr(task, "created_at")

    assert task.name == mock_task["name"]
    assert task.description == mock_task["description"]
    assert task.tools_available == mock_task["tools_available"]
    assert task.input_schema == mock_task["input_schema"]
    assert task.main == mock_task["main"]
    assert task.agent_id == mock_task["agent_id"]


@test("async tasks: tasks.get")
async def _(client=async_client, task=test_task_async):
    response = await client.tasks.get(task.id)
    assert isinstance(response, Task)

    assert task.name == response.name
    assert task.description == response.description
    assert task.tools_available == response.tools_available
    assert task.input_schema == response.input_schema
    assert task.main == response.main
    assert task.agent_id == response.agent_id


@test("async tasks: tasks.list")
async def _(client=async_client, _=test_task_async):
    response = await client.tasks.list()
    assert len(response) > 0
    assert isinstance(response[0], Task)


@test("async tasks: tasks.start_task_execution")
async def _(client=async_client, _=test_task_async):
    response = await client.tasks.start_task_execution(
        agent_id=uuid4(),
        task_id=uuid4(),
        arguments={},
        status="enqueued",
    )
    assert isinstance(response[0], Execution)


@test("async tasks: tasks.get_task_execution")
async def _(client=async_client, _=test_task_async):
    response = await client.tasks.get_task_execution(
        task_id=uuid4(),
        execution_id=uuid4(),
    )
    assert isinstance(response[0], List[Execution])
