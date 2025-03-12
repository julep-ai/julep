from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to get a paused execution token using latest_transitions
get_paused_execution_token_query = """
SELECT
    transition_id,
    created_at,
    execution_id,
    type,
    step_label,
    current_step,
    next_step,
    output,
    task_token,
    metadata
FROM latest_transitions
WHERE
    execution_id = $1
    AND type = 'wait'
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("execution", ["get_paused_execution_token"]))
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def get_paused_execution_token(
    *,
    execution_id: UUID,
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
        [execution_id],
        "fetchrow",
    )
