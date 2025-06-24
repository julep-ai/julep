from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import ExecutionStatusEvent
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to get execution status, updated timestamp, and error for a specific execution_id
get_execution_status_query = """
SELECT
    execution_id,
    status,
    updated_at,
    error,
    transition_count,
    metadata
FROM
    latest_executions
WHERE
    developer_id = $1 AND
    execution_id = $2
ORDER BY
    updated_at DESC
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("execution", ["get_status"]))
@wrap_in_class(ExecutionStatusEvent, one=True)
@pg_query
@beartype
async def get_execution_status(
    *,
    developer_id: UUID,
    execution_id: UUID,
) -> tuple[str, list, Literal["fetchrow"]]:
    """
    Get the current status, updated_at, and error for the given execution_id.

    Parameters:
        developer_id (UUID): The ID of the developer.
        execution_id (UUID): The ID of the execution.

    Returns:
        tuple[str, list, Literal["fetchrow"]]: SQL query and parameters for fetching execution status.
    """
    return (
        get_execution_status_query,
        [developer_id, execution_id],
        "fetchrow",
    )
