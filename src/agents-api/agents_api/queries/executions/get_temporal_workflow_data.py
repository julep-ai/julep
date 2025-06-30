from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to get temporal workflow data
get_temporal_workflow_data_query = """
SELECT id, run_id, result_run_id, first_execution_run_id FROM temporal_executions_lookup
WHERE
    execution_id = $1
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("temporal_execution", ["get"]))
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def get_temporal_workflow_data(
    *,
    execution_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Get temporal workflow data for a given execution.

    Parameters:
        execution_id (UUID): The ID of the execution.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for getting temporal workflow data.
    """
    # Executions are allowed direct GET access if they have execution_id
    execution_id = str(execution_id)

    return (
        get_temporal_workflow_data_query,
        [
            execution_id,
        ],
        "fetchrow",
    )
