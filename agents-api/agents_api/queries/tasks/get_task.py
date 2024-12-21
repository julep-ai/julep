from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException


from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class
from ...common.protocol.tasks import spec_to_task

get_task_query = """
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
    t.developer_id = $1 AND t.task_id = $2
    AND t.version = (
        SELECT MAX(version)
        FROM tasks
        WHERE developer_id = $1 AND task_id = $2
    )
GROUP BY t.developer_id, t.task_id, t.canonical_name, t.agent_id, t.version;
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
@wrap_in_class(spec_to_task, one=True)
@increase_counter("get_task")
@pg_query
@beartype
async def get_task(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Retrieves a task by its unique identifier along with its associated workflows.

    Parameters:
        developer_id (UUID): The unique identifier of the developer associated with the task.
        task_id (UUID): The unique identifier of the task to retrieve.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query, parameters, and fetch method.

    Raises:
        HTTPException: If developer/agent doesn't exist (404) or on unique constraint violation (409)
    """

    return (
        get_task_query,
        [developer_id, task_id],
        "fetchrow",
    )
