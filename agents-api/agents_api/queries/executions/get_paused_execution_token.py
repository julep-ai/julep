from datetime import timedelta
from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to get a paused execution token using latest_transitions
get_paused_execution_token_query = """
SELECT
    execution_id,
    transition_id,
    type,
    created_at,
    step_label,
    current_step,
    next_step,
    output,
    task_token,
    metadata
FROM latest_transitions
WHERE
    execution_id = $1
    AND created_at >= $2
    AND created_at >= (select created_at from executions where execution_id = $1 LIMIT 1)
    AND type = 'wait';
"""


@rewrap_exceptions(common_db_exceptions("execution", ["get_paused_execution_token"]))
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def get_paused_execution_token(
    *,
    execution_id: UUID,
    search_window: timedelta = timedelta(weeks=4),
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Get a paused execution token for a given execution.

    Parameters:
        execution_id (UUID): The ID of the execution.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for getting a paused execution token.
    """
    execution_id = str(execution_id)

    return (
        get_paused_execution_token_query,
        [execution_id, utcnow() - search_window],
        "fetchrow",
    )
