from typing import Any, Literal, TypeVar
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

# Query to get a paused execution token
get_paused_execution_token_query = parse_one("""
SELECT * FROM transitions
WHERE
    execution_id = $1
        AND type = 'wait'
    ORDER BY created_at DESC
    LIMIT 1;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException, 
            status_code=404,
            detail="No paused executions found for the specified task"
        ),
    }
)
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def get_paused_execution_token(
    *,
    developer_id: UUID,
    execution_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Get a paused execution token for a given execution.

    Parameters:
        developer_id (UUID): The ID of the developer.
        execution_id (UUID): The ID of the execution.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for getting a paused execution token.
    """
    execution_id = str(execution_id)

    # TODO: what to do with this query?
    # check_status_query = """
    # ?[execution_id, status] :=
    #     *executions:execution_id_status_idx {
    #         execution_id,
    #         status,
    #     },
    #     execution_id = to_uuid($execution_id),
    #     status = "awaiting_input"

    # :limit 1
    # :assert some
    # """

    return (
        get_paused_execution_token_query,
        [execution_id],
        "fetchrow",
    )

