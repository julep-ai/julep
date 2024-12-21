from typing import Any, Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException


from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class
from ...common.protocol.tasks import spec_to_task

list_tasks_query = """
SELECT 
    t.*, 
    COALESCE(
        jsonb_agg(
            CASE WHEN w.name IS NOT NULL THEN
                jsonb_build_object(
                    'name', w.name,
                    'steps', jsonb_build_array(
                        jsonb_build_object(
                            w.step_type, w.step_definition,
                            'step_idx', w.step_idx           -- Not sure if this is needed
                        )
                    )
                )
            END
        ) FILTER (WHERE w.name IS NOT NULL),
        '[]'::jsonb
    ) as workflows
FROM 
    tasks t
LEFT JOIN 
    workflows w ON t.developer_id = w.developer_id AND t.task_id = w.task_id AND t.version = w.version
WHERE 
    t.developer_id = $1
    {metadata_filter_query}
GROUP BY t.developer_id, t.task_id, t.canonical_name, t.agent_id, t.version
ORDER BY 
    CASE WHEN $4 = 'created_at' AND $5 = 'asc' THEN t.created_at END ASC NULLS LAST,
    CASE WHEN $4 = 'created_at' AND $5 = 'desc' THEN t.created_at END DESC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'asc' THEN t.updated_at END ASC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'desc' THEN t.updated_at END DESC NULLS LAST
LIMIT $2 OFFSET $3;
"""


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
@wrap_in_class(spec_to_task)
@increase_counter("list_tasks")
@pg_query
@beartype
async def list_tasks(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, list]:
    """
    Retrieves all tasks for a given developer with pagination and sorting.

    Parameters:
        developer_id (UUID): The unique identifier of the developer.
        limit (int): Maximum number of records to return (default: 100)
        offset (int): Number of records to skip (default: 0)
        sort_by (str): Field to sort by ("created_at" or "updated_at")
        direction (str): Sort direction ("asc" or "desc")
        metadata_filter (dict): Optional metadata filters

    Returns:
        tuple[str, list]: SQL query and parameters.

    Raises:
        HTTPException: If parameters are invalid or developer/agent doesn't exist
    """
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if limit > 100 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    # Format query with metadata filter if needed
    query = list_tasks_query.format(
        metadata_filter_query="AND metadata @> $6::jsonb" if metadata_filter else ""
    )

    # Build parameters list
    params = [
        developer_id,
        limit,
        offset,
        sort_by,
        direction,
    ]

    if metadata_filter:
        params.append(metadata_filter)

    return (query, params)
