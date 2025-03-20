from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Execution
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .constants import OUTPUT_UNNEST_KEY

# Query to get an execution using the latest_executions view
get_execution_query = """
SELECT
    developer_id,
    task_id,
    task_version,
    execution_id,
    input,
    metadata,
    created_at,
    updated_at,
    status,
    error,
    transition_count,
    output,
    current_step,
    next_step,
    step_label,
    task_token,
    transition_metadata
FROM
    latest_executions
WHERE
    execution_id = $1;
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
