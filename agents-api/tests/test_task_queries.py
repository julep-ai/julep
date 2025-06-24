# Tests for task queries

import pytest
from agents_api.autogen.openapi_model import (
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


async def test_query_create_task_sql(pg_dsn, test_developer_id, test_agent):
    """Test that a task can be successfully created."""

    pool = await create_db_pool(dsn=pg_dsn)
    task = await create_task(
        developer_id=test_developer_id,
        agent_id=test_agent.id,
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


async def test_query_create_or_update_task_sql(pg_dsn, test_developer_id, test_agent):
    """Test that a task can be successfully created or updated."""

    pool = await create_db_pool(dsn=pg_dsn)
    task = await create_or_update_task(
        developer_id=test_developer_id,
        agent_id=test_agent.id,
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


async def test_query_get_task_sql_exists(pg_dsn, test_developer_id, test_task):
    """Test that an existing task can be successfully retrieved."""

    pool = await create_db_pool(dsn=pg_dsn)

    # Then retrieve it
    result = await get_task(
        developer_id=test_developer_id,
        task_id=test_task.id,
        connection_pool=pool,
    )
    assert result is not None
    assert isinstance(result, Task), f"Result is not a Task, got {type(result)}"
    assert result.id == test_task.id
    assert result.name == "test task"
    assert result.description == "test task about"


async def test_query_get_task_sql_not_exists(pg_dsn, test_developer_id):
    """Test that attempting to retrieve a non-existent task raises an error."""

    pool = await create_db_pool(dsn=pg_dsn)
    task_id = uuid7()

    with pytest.raises(HTTPException) as exc:
        await get_task(
            developer_id=test_developer_id,
            task_id=task_id,
            connection_pool=pool,
        )

    assert exc.value.status_code == 404
    assert "Task not found" in str(exc.value.detail)


async def test_query_delete_task_sql_exists(pg_dsn, test_developer_id, test_task):
    """Test that a task can be successfully deleted."""

    pool = await create_db_pool(dsn=pg_dsn)

    # First verify task exists
    result = await get_task(
        developer_id=test_developer_id,
        task_id=test_task.id,
        connection_pool=pool,
    )
    assert result is not None
    assert result.id == test_task.id

    # Delete the task
    deleted = await delete_task(
        developer_id=test_developer_id,
        task_id=test_task.id,
        connection_pool=pool,
    )
    assert deleted is not None
    assert deleted.id == test_task.id

    # Verify task no longer exists
    with pytest.raises(HTTPException) as exc:
        await get_task(
            developer_id=test_developer_id,
            task_id=test_task.id,
            connection_pool=pool,
        )

    assert exc.value.status_code == 404
    assert "Task not found" in str(exc.value.detail)


async def test_query_delete_task_sql_not_exists(pg_dsn, test_developer_id):
    """Test that attempting to delete a non-existent task raises an error."""

    pool = await create_db_pool(dsn=pg_dsn)
    task_id = uuid7()

    with pytest.raises(HTTPException) as exc:
        await delete_task(
            developer_id=test_developer_id,
            task_id=task_id,
            connection_pool=pool,
        )

    assert exc.value.status_code == 404
    assert "Task not found" in str(exc.value.detail)


# Add tests for list tasks
async def test_query_list_tasks_sql_with_filters(pg_dsn, test_developer_id, test_agent):
    """Test that tasks can be successfully filtered and retrieved."""

    pool = await create_db_pool(dsn=pg_dsn)
    result = await list_tasks(
        developer_id=test_developer_id,
        agent_id=test_agent.id,
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


async def test_query_list_tasks_sql_no_filters(
    pg_dsn, test_developer_id, test_agent, test_task
):
    """Test that a list of tasks can be successfully retrieved."""

    pool = await create_db_pool(dsn=pg_dsn)
    result = await list_tasks(
        developer_id=test_developer_id,
        agent_id=test_agent.id,
        connection_pool=pool,
    )
    assert result is not None, "Result is None"
    assert isinstance(result, list), f"Result is not a list, got {type(result)}"
    assert len(result) > 0, "Result is empty"
    assert all(isinstance(task, Task) for task in result), (
        "Not all listed tasks are of type Task"
    )


async def test_query_list_tasks_sql_invalid_limit(
    pg_dsn, test_developer_id, test_agent, test_task
):
    """Test that listing tasks with an invalid limit raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_tasks(
            developer_id=test_developer_id,
            agent_id=test_agent.id,
            connection_pool=pool,
            limit=101,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"

    with pytest.raises(HTTPException) as exc:
        await list_tasks(
            developer_id=test_developer_id,
            agent_id=test_agent.id,
            connection_pool=pool,
            limit=0,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Limit must be between 1 and 100"


async def test_query_list_tasks_sql_invalid_offset(
    pg_dsn, test_developer_id, test_agent, test_task
):
    """Test that listing tasks with an invalid offset raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_tasks(
            developer_id=test_developer_id,
            agent_id=test_agent.id,
            connection_pool=pool,
            offset=-1,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Offset must be >= 0"


async def test_query_list_tasks_sql_invalid_sort_by(
    pg_dsn, test_developer_id, test_agent, test_task
):
    """Test that listing tasks with an invalid sort by raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_tasks(
            developer_id=test_developer_id,
            agent_id=test_agent.id,
            connection_pool=pool,
            sort_by="invalid",
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort field"


async def test_query_list_tasks_sql_invalid_sort_direction(
    pg_dsn, test_developer_id, test_agent, test_task
):
    """Test that listing tasks with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=pg_dsn)
    with pytest.raises(HTTPException) as exc:
        await list_tasks(
            developer_id=test_developer_id,
            agent_id=test_agent.id,
            connection_pool=pool,
            direction="invalid",
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid sort direction"


async def test_query_update_task_sql_exists(pg_dsn, test_developer_id, test_agent, test_task):
    """Test that a task can be successfully updated."""

    pool = await create_db_pool(dsn=pg_dsn)
    updated = await update_task(
        developer_id=test_developer_id,
        task_id=test_task.id,
        agent_id=test_agent.id,
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
    assert updated.id == test_task.id

    # Verify task was updated
    updated_task = await get_task(
        developer_id=test_developer_id,
        task_id=test_task.id,
        connection_pool=pool,
    )
    assert updated_task.name == "updated task"
    assert updated_task.description == "updated task description"
    assert updated_task.metadata == {"updated": True}


async def test_query_update_task_sql_not_exists(pg_dsn, test_developer_id, test_agent):
    """Test that attempting to update a non-existent task raises an error."""

    pool = await create_db_pool(dsn=pg_dsn)
    task_id = uuid7()

    with pytest.raises(HTTPException) as exc:
        await update_task(
            developer_id=test_developer_id,
            task_id=task_id,
            agent_id=test_agent.id,
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

    assert exc.value.status_code == 404
    assert "Task not found" in str(exc.value.detail)


async def test_query_patch_task_sql_exists(pg_dsn, test_developer_id, test_agent):
    """Test that patching an existing task works correctly."""
    pool = await create_db_pool(dsn=pg_dsn)

    # Create initial task
    task = await create_task(
        developer_id=test_developer_id,
        agent_id=test_agent.id,
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
        developer_id=test_developer_id,
        task_id=task.id,
        agent_id=test_agent.id,
        data=PatchTaskRequest(name="patched task", metadata={"patched": True}),
        connection_pool=pool,
    )

    assert updated is not None
    assert isinstance(updated, Task)
    assert updated.id == task.id

    # Verify task was patched correctly
    patched_task = await get_task(
        developer_id=test_developer_id,
        task_id=task.id,
        connection_pool=pool,
    )
    # Check that patched fields were updated
    assert patched_task.name == "patched task"
    assert patched_task.metadata == {"patched": True}
    # Check that non-patched fields remain unchanged
    assert patched_task.canonical_name == "test_task"
    assert patched_task.description == "test task description"


async def test_query_patch_task_sql_not_exists(pg_dsn, test_developer_id, test_agent):
    """Test that attempting to patch a non-existent task raises an error."""
    pool = await create_db_pool(dsn=pg_dsn)
    task_id = uuid7()

    with pytest.raises(HTTPException) as exc:
        await patch_task(
            developer_id=test_developer_id,
            task_id=task_id,
            agent_id=test_agent.id,
            data=PatchTaskRequest(name="patched task", metadata={"patched": True}),
            connection_pool=pool,
        )

    assert exc.value.status_code == 404
    assert "Task not found" in str(exc.value.detail)
