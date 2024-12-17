"""This module contains functions for querying session data from the PostgreSQL database."""

from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
raw_query = """
SELECT COUNT(session_id) as count
FROM sessions
WHERE developer_id = $1;
"""

# Parse and optimize the query
query = parse_one(raw_query).sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        )
    }
)
@wrap_in_class(dict, one=True)
@increase_counter("count_sessions")
@pg_query
@beartype
async def count_sessions(
    *,
    developer_id: UUID,
) -> tuple[str, list]:
    """
    Counts sessions from the PostgreSQL database.
    Uses the index on developer_id for efficient counting.

    Args:
        developer_id (UUID): The developer's ID to filter sessions by.

    Returns:
        tuple[str, list]: SQL query and parameters.
    """

    return (
        query,
        [developer_id],
    ) 