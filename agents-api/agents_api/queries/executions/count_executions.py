from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Query to count executions for a given task
execution_count_query = parse_one("""
SELECT COUNT(*) FROM latest_executions
WHERE
    developer_id = $1
    AND task_id = $2;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="No executions found for the specified task",
        ),
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or task does not exist",
        ),
    }
)
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def count_executions(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Count the number of executions for a given task.

    Parameters:
        developer_id (UUID): The ID of the developer.
        task_id (UUID): The ID of the task.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for counting executions.
    """
    return (
        execution_count_query,
        [developer_id, task_id],
        "fetchrow",
    )
