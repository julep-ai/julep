import uuid
from typing import List

from julep.api.types import Execution, Task
from ward import test

from tests.fixtures import agent, async_client, client, task


@test("create task")
def _(client=client, agent=agent):
    task = client.tasks.create(
        agent_id=agent.id,
        name="task1",
        description="task 1",
        tools_available=["tool1"],
        input_schema={},
        main=[],
    )

    assert isinstance(task, Task)
    assert task.created_at
    assert bool(uuid.UUID(str(task.id), version=4))

    assert task.agent_id == agent.id
    assert task.name == "task1"
    assert task.description == "task 1"
    assert task.tools_available == ["tool1"]
    assert task.input_schema == {}
    assert task.main == []


@test("get task")
def _(client=client, agent=agent, task=task):
    task = client.tasks.get(
        agent_id=agent.id,
        task_id=task.id,
    )

    assert isinstance(task, Task)
    assert task.created_at
    assert bool(uuid.UUID(str(task.id), version=4))

    assert task.agent_id == agent.id
    assert task.name == "task1"
    assert task.description == "task 1"
    assert task.tools_available == ["tool1"]
    assert task.input_schema == {}
    assert task.main == []


@test("list task")
def _(client=client, agent=agent):
    tasks = client.tasks.list(
        agent_id=agent.id,
    )

    assert isinstance(tasks, List[Task])
    assert len(tasks) > 0

    task = tasks[0]

    assert task.created_at
    assert bool(uuid.UUID(str(task.id), version=4))

    assert task.agent_id == agent.id
    assert task.name == "task1"
    assert task.description == "task 1"
    assert task.tools_available == ["tool1"]
    assert task.input_schema == {}
    assert task.main == []


@test("start task execution")
def _(client=client, agent=agent, task=task):
    execution = client.tasks.start_task_execution(
        agent_id=agent.id,
        task_id=task.id,
        arguments={},
        status="enqueued",
    )

    assert isinstance(execution, Execution)


@test("create task")
async def _(client=async_client, agent=agent):
    task = await client.tasks.create(
        agent_id=agent.id,
        name="task1",
        description="task 1",
        tools_available=["tool1"],
        input_schema={},
        main=[],
    )

    assert isinstance(task, Task)
    assert task.created_at
    assert bool(uuid.UUID(str(task.id), version=4))

    assert task.agent_id == agent.id
    assert task.name == "task1"
    assert task.description == "task 1"
    assert task.tools_available == ["tool1"]
    assert task.input_schema == {}
    assert task.main == []


@test("get task")
async def _(client=async_client, agent=agent, task=task):
    task = await client.tasks.get(
        agent_id=agent.id,
        task_id=task.id,
    )

    assert isinstance(task, Task)
    assert task.created_at
    assert bool(uuid.UUID(str(task.id), version=4))

    assert task.agent_id == agent.id
    assert task.name == "task1"
    assert task.description == "task 1"
    assert task.tools_available == ["tool1"]
    assert task.input_schema == {}
    assert task.main == []


@test("list task")
async def _(client=async_client, agent=agent):
    tasks = await client.tasks.list(
        agent_id=agent.id,
    )

    assert isinstance(tasks, List[Task])
    assert len(tasks) > 0

    task = tasks[0]

    assert task.created_at
    assert bool(uuid.UUID(str(task.id), version=4))

    assert task.agent_id == agent.id
    assert task.name == "task1"
    assert task.description == "task 1"
    assert task.tools_available == ["tool1"]
    assert task.input_schema == {}
    assert task.main == []


@test("start task execution")
async def _(client=async_client, agent=agent, task=task):
    execution = await client.tasks.start_task_execution(
        agent_id=agent.id,
        task_id=task.id,
        arguments={},
        status="enqueued",
    )

    assert isinstance(execution, Execution)
