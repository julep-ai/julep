from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to lookup temporal data
lookup_temporal_data_query = """
SELECT t.*
FROM
    temporal_executions_lookup t
    JOIN latest_executions e ON t.execution_id = e.execution_id
WHERE
    e.execution_id = $1
    AND e.developer_id = $2
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("temporal_execution", ["get"]))
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def lookup_temporal_data(
    *,
    developer_id: UUID,
    execution_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Lookup temporal data for a given execution.

    Parameters:
        developer_id (UUID): The ID of the developer.
        execution_id (UUID): The ID of the execution.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for looking up temporal data.
    """
    developer_id = str(developer_id)
    execution_id = str(execution_id)

    return (
        lookup_temporal_data_query,
        [execution_id, developer_id],
        "fetchrow",
    )
