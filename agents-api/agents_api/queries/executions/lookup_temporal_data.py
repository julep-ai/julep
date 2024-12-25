from typing import Any, Literal, TypeVar
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Query to lookup temporal data
lookup_temporal_data_query = parse_one("""
SELECT * FROM temporal_executions_lookup
WHERE
    execution_id = $1
LIMIT 1;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException, 
            status_code=404,
            detail="No temporal data found for the specified execution"
        ),
    }
)
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def lookup_temporal_data(
    *,
    developer_id: UUID,  # TODO: what to do with this parameter?
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
        [execution_id],
        "fetchrow",
    )
