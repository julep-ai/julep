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
# FIXME: order by updated_at as well
# FIXME: return to latest_executions view once latest_transitions is fixed
list_executions_query = """
SELECT
    e.developer_id,
    e.task_id,
    e.task_version,
    e.execution_id,
    e.input,
    e.metadata,
    e.created_at,
    coalesce(lt.created_at, e.created_at) AS updated_at,
    CASE
        WHEN lt.type::text IS NULL THEN 'queued'
        WHEN lt.type::text = 'init' THEN 'starting'
        WHEN lt.type::text = 'init_branch' THEN 'running'
        WHEN lt.type::text = 'wait' THEN 'awaiting_input'
        WHEN lt.type::text = 'resume' THEN 'running'
        WHEN lt.type::text = 'step' THEN 'running'
        WHEN lt.type::text = 'finish' THEN 'succeeded'
        WHEN lt.type::text = 'finish_branch' THEN 'running'
        WHEN lt.type::text = 'error' THEN 'failed'
        WHEN lt.type::text = 'cancelled' THEN 'cancelled'
        ELSE 'queued'
    END AS status,
    CASE
        WHEN lt.type::text = 'error' THEN lt.output ->> 'error'
        ELSE NULL
    END AS error,
    coalesce(lt.output, '{}'::jsonb) AS output,
    lt.current_step,
    lt.next_step,
    lt.step_label,
    lt.task_token,
    lt.metadata AS transition_metadata
FROM
    executions e
    LEFT JOIN LATERAL (
        SELECT *
        FROM transitions t
        WHERE t.execution_id = e.execution_id
        ORDER BY t.created_at DESC
        LIMIT 1
    ) lt ON true
WHERE
    e.developer_id = $1 AND
    e.task_id = $2
ORDER BY
    CASE WHEN $3 = 'asc' THEN e.created_at END ASC NULLS LAST,
    CASE WHEN $3 = 'desc' THEN e.created_at END DESC NULLS LAST
    -- CASE WHEN $3 = 'updated_at' AND $4 = 'asc' THEN e.updated_at END ASC NULLS LAST,
    -- CASE WHEN $3 = 'updated_at' AND $4 = 'desc' THEN e.updated_at END DESC NULLS LAST
LIMIT $4 OFFSET $5;
"""


@rewrap_exceptions({
    asyncpg.InvalidRowCountInLimitClauseError: partialclass(
        HTTPException,
        status_code=400,
        detail="Invalid limit clause",
    ),
    asyncpg.InvalidRowCountInResultOffsetClauseError: partialclass(
        HTTPException,
        status_code=400,
        detail="Invalid offset clause",
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

    # Validate parameters
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if sort_by not in ["created_at", "updated_at"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be greater than 0")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    return (
        list_executions_query,
        [
            developer_id,
            task_id,
            # sort_by,
            direction,
            limit,
            offset,
        ],
    )
