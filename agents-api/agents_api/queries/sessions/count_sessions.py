"""This module contains functions for querying session data from the PostgreSQL database."""

from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
session_query = """
SELECT COUNT(*)
FROM sessions
WHERE developer_id = $1;
"""


@rewrap_exceptions(common_db_exceptions("session", ["count"]))
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
        session_query,
        [developer_id],
    )
