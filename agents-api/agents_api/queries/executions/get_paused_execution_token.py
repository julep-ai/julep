from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Query to get a paused execution token
get_paused_execution_token_query = """
SELECT * FROM latest_transitions
WHERE
    execution_id = $1
        AND type = 'wait'
    ORDER BY created_at DESC
    LIMIT 1;
"""


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="No paused executions found for the specified task",
        ),
    }
)
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
