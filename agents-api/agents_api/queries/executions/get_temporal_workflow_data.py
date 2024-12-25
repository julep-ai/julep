from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Query to get temporal workflow data
get_temporal_workflow_data_query = parse_one("""
SELECT id, run_id, result_run_id, first_execution_run_id FROM temporal_executions_lookup
WHERE
    execution_id = $1
LIMIT 1;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="No temporal workflow data found for the specified execution",
        ),
    }
)
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
