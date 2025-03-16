from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Execution
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .constants import OUTPUT_UNNEST_KEY

# Query to get an execution
get_execution_query = """
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
    tc.count as transition_count,
    lt.next_step,
    lt.step_label,
    lt.task_token,
    lt.metadata AS transition_metadata
FROM
    executions e
    LEFT JOIN transitions lt ON e.execution_id = lt.execution_id
    CROSS JOIN LATERAL (
        SELECT COUNT(*) as count
        FROM transitions t
        WHERE t.execution_id = e.execution_id
    ) tc
WHERE e.execution_id = $1
ORDER BY lt.created_at DESC
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("execution", ["get"]))
@wrap_in_class(
    Execution,
    one=True,
    transform=lambda d: {
        "id": d.pop("execution_id"),
        **d,
        "output": d["output"][OUTPUT_UNNEST_KEY]
        if isinstance(d["output"], dict) and OUTPUT_UNNEST_KEY in d["output"]
        else d["output"],
        "metadata": {
            **({"transitions": d["transition_metadata"]} if d["transition_metadata"] else {}),
            "transition_count": d["transition_count"],
        },
    },
)
@pg_query
@beartype
async def get_execution(
    *,
    execution_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Get an execution by its ID.

    Parameters:
        execution_id (UUID): The ID of the execution.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for getting the execution.
    """
    return (
        get_execution_query,
        [execution_id],
        "fetchrow",
    )
