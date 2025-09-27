# Tests for task queries

from agents_api.autogen.openapi_model import (
    CreateOrUpdateTaskRequest,
    CreateTaskRequest,
    PatchTaskRequest,
    Task,
    UpdateTaskRequest,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.tasks.create_or_update_task import create_or_update_task
from agents_api.queries.tasks.create_task import create_task
from agents_api.queries.tasks.delete_task import delete_task
from agents_api.queries.tasks.get_task import get_task
from agents_api.queries.tasks.list_tasks import list_tasks
from agents_api.queries.tasks.patch_task import patch_task
from agents_api.queries.tasks.update_task import update_task
from fastapi import HTTPException
from uuid_extensions import uuid7
from ward import raises, test

from tests.fixtures import pg_dsn, test_agent, test_developer_id, test_task


@test("query: create task sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that a task can be successfully created."""

    pool = await create_db_pool(dsn=dsn)
    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=uuid7(),
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"hi": "_"}}],
        ),
        connection_pool=pool,
    )

    assert isinstance(task, Task)
    assert task.id is not None
    assert task.main is not None


@test("query: create or update task sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that a task can be successfully created or updated."""

    pool = await create_db_pool(dsn=dsn)
    task = await create_or_update_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=uuid7(),
        data=CreateTaskRequest(
            name="test task",
            description="test task about",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"hi": "_"}}],
        ),
        connection_pool=pool,
    )

    assert isinstance(task, Task)
    assert task.id is not None
    assert task.main is not None


@test("query: get task sql - exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
    """Test that an existing task can be successfully retrieved."""

    pool = await create_db_pool(dsn=dsn)

    # Then retrieve it
    result = await get_task(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )
    assert result is not None
    assert isinstance(result, Task), f"Result is not a Task, got {type(result)}"
    assert result.id == task.id
    assert result.name == "test task"
    assert result.description == "test task about"


@test("query: get task sql - not exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that attempting to retrieve a non-existent task raises an error."""

    pool = await create_db_pool(dsn=dsn)
    task_id = uuid7()

    with raises(HTTPException) as exc:
        await get_task(
            developer_id=developer_id,
            task_id=task_id,
            connection_pool=pool,
        )

    assert exc.raised.status_code == 404
    assert "Task not found" in str(exc.raised.detail)


@test("query: delete task sql - exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, task=test_task):
    """Test that a task can be successfully deleted."""

    pool = await create_db_pool(dsn=dsn)

    # First verify task exists
    result = await get_task(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )
    assert result is not None
    assert result.id == task.id

    # Delete the task
    deleted = await delete_task(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )
    assert deleted is not None
    assert deleted.id == task.id

    # Verify task no longer exists
    with raises(HTTPException) as exc:
        await get_task(
            developer_id=developer_id,
            task_id=task.id,
            connection_pool=pool,
        )

    assert exc.raised.status_code == 404
    assert "Task not found" in str(exc.raised.detail)


@test("query: delete task sql - not exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that attempting to delete a non-existent task raises an error."""

    pool = await create_db_pool(dsn=dsn)
    task_id = uuid7()

    with raises(HTTPException) as exc:
        await delete_task(
            developer_id=developer_id,
            task_id=task_id,
            connection_pool=pool,
        )

    assert exc.raised.status_code == 404
    assert "Task not found" in str(exc.raised.detail)


# Add tests for list tasks
@test("query: list tasks sql - with filters")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that tasks can be successfully filtered and retrieved."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_tasks(
        developer_id=developer_id,
        agent_id=agent.id,
        limit=10,
        offset=0,
        sort_by="updated_at",
        direction="asc",
        metadata_filter={"test": True},
        connection_pool=pool,
    )
    assert result is not None
    assert isinstance(result, list)
    assert all(isinstance(task, Task) for task in result)
    assert all(task.metadata.get("test") is True for task in result)


@test("query: list tasks sql - no filters")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, task=test_task):
    """Test that a list of tasks can be successfully retrieved."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_tasks(
        developer_id=developer_id,
        agent_id=agent.id,
        connection_pool=pool,
    )
    assert result is not None, "Result is None"
    assert isinstance(result, list), f"Result is not a list, got {type(result)}"
    assert len(result) > 0, "Result is empty"
    assert all(isinstance(task, Task) for task in result), (
        "Not all listed tasks are of type Task"
    )


@test("query: list tasks sql, invalid limit")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, task=test_task):
    """Test that listing tasks with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_tasks(
            developer_id=developer_id,
            agent_id=agent.id,
            connection_pool=pool,
            limit=101,
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"

    with raises(HTTPException) as exc:
        await list_tasks(
            developer_id=developer_id,
            agent_id=agent.id,
            connection_pool=pool,
            limit=0,
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Limit must be between 1 and 100"


@test("query: list tasks sql, invalid offset")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, task=test_task):
    """Test that listing tasks with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_tasks(
            developer_id=developer_id,
            agent_id=agent.id,
            connection_pool=pool,
            offset=-1,
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Offset must be >= 0"


@test("query: list tasks sql, invalid sort by")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, task=test_task):
    """Test that listing tasks with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_tasks(
            developer_id=developer_id,
            agent_id=agent.id,
            connection_pool=pool,
            sort_by="invalid",
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort field"


@test("query: list tasks sql, invalid sort direction")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, task=test_task):
    """Test that listing tasks with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with raises(HTTPException) as exc:
        await list_tasks(
            developer_id=developer_id,
            agent_id=agent.id,
            connection_pool=pool,
            direction="invalid",
        )
    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


@test("query: update task sql - exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, task=test_task):
    """Test that a task can be successfully updated."""

    pool = await create_db_pool(dsn=dsn)
    updated = await update_task(
        developer_id=developer_id,
        task_id=task.id,
        agent_id=agent.id,
        data=UpdateTaskRequest(
            name="updated task",
            canonical_name="updated_task",
            description="updated task description",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"hi": "_"}}],
            inherit_tools=False,
            metadata={"updated": True},
        ),
        connection_pool=pool,
    )

    assert updated is not None
    assert isinstance(updated, Task)
    assert updated.id == task.id

    # Verify task was updated
    updated_task = await get_task(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )
    assert updated_task.name == "updated task"
    assert updated_task.description == "updated task description"
    assert updated_task.metadata == {"updated": True}


@test("query: update task sql - not exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that attempting to update a non-existent task raises an error."""

    pool = await create_db_pool(dsn=dsn)
    task_id = uuid7()

    with raises(HTTPException) as exc:
        await update_task(
            developer_id=developer_id,
            task_id=task_id,
            agent_id=agent.id,
            data=UpdateTaskRequest(
                canonical_name="updated_task",
                name="updated task",
                description="updated task description",
                input_schema={"type": "object", "additionalProperties": True},
                main=[{"evaluate": {"hi": "_"}}],
                inherit_tools=False,
            ),
            connection_pool=pool,
        )

    assert exc.raised.status_code == 404
    assert "Task not found" in str(exc.raised.detail)


@test("query: patch task sql - exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that patching an existing task works correctly."""
    pool = await create_db_pool(dsn=dsn)

    # Create initial task
    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        data=CreateTaskRequest(
            canonical_name="test_task",
            name="test task",
            description="test task description",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"hi": "_"}}],
            inherit_tools=False,
            metadata={"initial": True},
        ),
        connection_pool=pool,
    )

    # Patch the task
    updated = await patch_task(
        developer_id=developer_id,
        task_id=task.id,
        agent_id=agent.id,
        data=PatchTaskRequest(name="patched task", metadata={"patched": True}),
        connection_pool=pool,
    )

    assert updated is not None
    assert isinstance(updated, Task)
    assert updated.id == task.id

    # Verify task was patched correctly
    patched_task = await get_task(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )
    # Check that patched fields were updated
    assert patched_task.name == "patched task"
    assert patched_task.metadata == {"patched": True}
    # Check that non-patched fields remain unchanged
    assert patched_task.canonical_name == "test_task"
    assert patched_task.description == "test task description"


@test("query: patch task sql - not exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that attempting to patch a non-existent task raises an error."""
    pool = await create_db_pool(dsn=dsn)
    task_id = uuid7()

    with raises(HTTPException) as exc:
        await patch_task(
            developer_id=developer_id,
            task_id=task_id,
            agent_id=agent.id,
            data=PatchTaskRequest(name="patched task", metadata={"patched": True}),
            connection_pool=pool,
        )

    assert exc.raised.status_code == 404
    assert "Task not found" in str(exc.raised.detail)


@test("query: get task with workflows and tools - no cartesian product")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that getting a task with both workflows and tools doesn't create duplicates."""

    pool = await create_db_pool(dsn=dsn)

    # Create a task with workflows
    task = await create_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=uuid7(),
        data=CreateTaskRequest(
            name="test task with workflows",
            description="test task with multiple workflows and tools",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"result": "_"}}],
            tools=[
                {
                    "type": "function",
                    "name": "workflow1",
                    "function": {"name": "workflow1", "parameters": {"type": "object"}},
                },
                {
                    "type": "function",
                    "name": "workflow2",
                    "function": {"name": "workflow2", "parameters": {"type": "object"}},
                },
            ],
        ),
        connection_pool=pool,
    )

    # Get the task
    result = await get_task(
        developer_id=developer_id,
        task_id=task.id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Task)

    # Verify we have the correct number of tools (no duplicates)
    assert len(result.tools) == 2, f"Expected 2 tools, got {len(result.tools)}"
    tool_names = [tool.name for tool in result.tools]
    assert set(tool_names) == {"workflow1", "workflow2"}, "Tool names don't match"


@test("query: get task filters tools by updated_at timestamp")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that tools not updated for the current task version are filtered out."""

    pool = await create_db_pool(dsn=dsn)

    # Create a task v1 with a tool
    task_id = uuid7()
    canonical_name = "test_task_tool_lifecycle"

    # V1: Create task with tool_a
    await create_or_update_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=task_id,
        data=CreateOrUpdateTaskRequest(
            name="task v1",
            canonical_name=canonical_name,
            description="initial task version with tool",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"result": "v1"}}],
            tools=[
                {
                    "type": "function",
                    "name": "tool_a",
                    "function": {
                        "name": "tool_a",
                        "description": "Tool A",
                        "parameters": {"type": "object"},
                    },
                }
            ],
        ),
        connection_pool=pool,
    )

    # Check v1 has the tool
    result_v1 = await get_task(
        developer_id=developer_id,
        task_id=task_id,
        connection_pool=pool,
    )
    assert result_v1 is not None
    assert result_v1.version == 1
    tool_names_v1 = [tool.name for tool in result_v1.tools]
    assert "tool_a" in tool_names_v1, "Tool A should be present in v1"
    assert len(result_v1.tools) == 1, f"Expected 1 tool in v1, got {len(result_v1.tools)}"

    # Wait to ensure different timestamps
    import asyncio

    await asyncio.sleep(0.1)

    # V2: Update to remove the tool
    await create_or_update_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=task_id,
        data=CreateOrUpdateTaskRequest(
            name="task v2",
            canonical_name=canonical_name,
            description="v2 without tool_a",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"result": "v2"}}],
            tools=[],  # No tools in v2
            inherit_tools=False,
        ),
        connection_pool=pool,
    )

    # Check v2 - tool_a should be filtered out because its updated_at is older
    result_v2 = await get_task(
        developer_id=developer_id,
        task_id=task_id,
        connection_pool=pool,
    )
    assert result_v2 is not None
    assert result_v2.version == 2
    tool_names_v2 = [tool.name for tool in result_v2.tools]
    assert "tool_a" not in tool_names_v2, "Tool A should be filtered out in v2"
    assert len(result_v2.tools) == 0, f"Expected 0 tools in v2, got {len(result_v2.tools)}"

    # Wait to ensure different timestamps
    await asyncio.sleep(0.1)

    # V3: Re-add the same tool
    await create_or_update_task(
        developer_id=developer_id,
        agent_id=agent.id,
        task_id=task_id,
        data=CreateOrUpdateTaskRequest(
            name="task v3",
            canonical_name=canonical_name,
            description="v3 with tool_a re-added",
            input_schema={"type": "object", "additionalProperties": True},
            main=[{"evaluate": {"result": "v3"}}],
            tools=[
                {
                    "type": "function",
                    "name": "tool_a",
                    "function": {
                        "name": "tool_a",
                        "description": "Tool A",
                        "parameters": {"type": "object"},
                    },
                }
            ],
        ),
        connection_pool=pool,
    )

    # Check v3 - tool_a should be present again because it was updated
    result_v3 = await get_task(
        developer_id=developer_id,
        task_id=task_id,
        connection_pool=pool,
    )
    assert result_v3 is not None
    assert result_v3.version == 3
    tool_names_v3 = [tool.name for tool in result_v3.tools]
    assert "tool_a" in tool_names_v3, "Tool A should be present again in v3"
    assert len(result_v3.tools) == 1, f"Expected 1 tool in v3, got {len(result_v3.tools)}"
