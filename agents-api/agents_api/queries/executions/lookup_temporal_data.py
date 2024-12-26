from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# FIXME: Check if this query is correct


# Query to lookup temporal data
lookup_temporal_data_query = """
SELECT t.*
FROM
    temporal_executions_lookup t,
    executions e
WHERE
    t.execution_id = e.execution_id
    AND e.execution_id = $1
    AND e.developer_id = $2
LIMIT 1;
"""


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="No temporal data found for the specified execution",
        ),
    }
)
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
