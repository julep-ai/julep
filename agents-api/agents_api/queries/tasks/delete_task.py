from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for deleting workflows
workflow_query = parse_one("""
DELETE FROM workflows
WHERE developer_id = $1 AND task_id = $2;
""").sql(pretty=True)

# Define the raw SQL query for deleting tasks
task_query = parse_one("""
DELETE FROM tasks
WHERE developer_id = $1 AND task_id = $2
RETURNING task_id;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or agent does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="A task with this ID already exists for this agent.",
        ),
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="Task not found",
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["task_id"],
        "deleted_at": utcnow(),
    },
)
@pg_query
@beartype
async def delete_task(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]:
    """
    Deletes a task by its unique identifier along with its associated workflows.

    Parameters:
        developer_id (UUID): The unique identifier of the developer associated with the task.
        task_id (UUID): The unique identifier of the task to delete.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query, parameters, and fetch method.

    Raises:
        HTTPException: If developer/agent doesn't exist (404) or on unique constraint violation (409)
    """

    return [
        (workflow_query, [developer_id, task_id], "fetch"),
        (task_query, [developer_id, task_id], "fetchrow"),
    ]
