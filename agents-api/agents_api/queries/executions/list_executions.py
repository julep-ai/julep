from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Execution
from ...common.utils.db_exceptions import common_db_exceptions, partialclass
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .constants import OUTPUT_UNNEST_KEY

# Query to list executions
list_executions_query = """
SELECT * FROM latest_executions
WHERE
    developer_id = $1 AND
    task_id = $2
ORDER BY
    CASE WHEN $3 = 'created_at' AND $4 = 'asc' THEN created_at END ASC NULLS LAST,
    CASE WHEN $3 = 'created_at' AND $4 = 'desc' THEN created_at END DESC NULLS LAST,
    CASE WHEN $3 = 'updated_at' AND $4 = 'asc' THEN updated_at END ASC NULLS LAST,
    CASE WHEN $3 = 'updated_at' AND $4 = 'desc' THEN updated_at END DESC NULLS LAST
LIMIT $5 OFFSET $6;
"""


@rewrap_exceptions({
    asyncpg.InvalidRowCountInLimitClauseError: partialclass(
        HTTPException, status_code=400, detail="Invalid limit clause"
    ),
    asyncpg.InvalidRowCountInResultOffsetClauseError: partialclass(
        HTTPException, status_code=400, detail="Invalid offset clause"
    ),
    **common_db_exceptions("execution", ["list"]),
})
@wrap_in_class(
    Execution,
    transform=lambda d: {
        "id": d.pop("execution_id"),
        **d,
        "output": d["output"][OUTPUT_UNNEST_KEY]
        if isinstance(d.get("output"), dict) and OUTPUT_UNNEST_KEY in d["output"]
        else d.get("output"),
    },
)
@pg_query
@beartype
async def list_executions(
    *,
    developer_id: UUID,
    task_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, list]:
    """
    List executions for a given task.

    Parameters:
        developer_id (UUID): The ID of the developer.
        task_id (UUID): The ID of the task.
        limit (int): The number of executions to return.
        offset (int): The number of executions to skip.
        sort_by (Literal["created_at", "updated_at"]): The field to sort by.
        direction (Literal["asc", "desc"]): The direction to sort by.

    Returns:
        tuple[str, list]: SQL query and parameters for listing executions.
    """

    if sort_by not in ["created_at", "updated_at"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if limit > 100 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be >= 0")

    return (
        list_executions_query,
        [
            developer_id,
            task_id,
            sort_by,
            direction,
            limit,
            offset,
        ],
    )
