from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.protocol.models import spec_to_task
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# AIDEV-NOTE: Tools aggregated in subquery to avoid cartesian product; filtered by updated_at to exclude older versions
# Define the raw SQL query for getting a task
get_task_query = """
SELECT
    t.*,
    COALESCE(
        jsonb_agg(
            DISTINCT jsonb_build_object(
                'name', w.name,
                'steps', (
                    SELECT jsonb_agg(step_definition ORDER BY step_idx)
                    FROM workflows w2
                    WHERE w2.developer_id = w.developer_id
                    AND w2.task_id = w.task_id
                    AND w2.version = w.version
                    AND w2.name = w.name
                )
            )
        ) FILTER (WHERE w.name IS NOT NULL),
        '[]'::jsonb
    ) as workflows,
    COALESCE(
        (
            SELECT jsonb_agg(to_jsonb(tl))
            FROM tools tl
            WHERE tl.developer_id = t.developer_id
            AND tl.task_id = t.task_id
            AND tl.updated_at >= t.updated_at
        ),
        '[]'::jsonb
    ) as tools
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


@rewrap_exceptions(common_db_exceptions("task", ["get"]))
@wrap_in_class(spec_to_task, one=True)
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
