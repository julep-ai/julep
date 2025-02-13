"""This module contains the implementation for deleting sessions from the PostgreSQL database."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL queries
lookup_query = """
DELETE FROM session_lookup
WHERE developer_id = $1 AND session_id = $2;
"""

session_query = """
DELETE FROM sessions
WHERE developer_id = $1 AND session_id = $2
RETURNING session_id AS id;
"""


@rewrap_exceptions(common_db_exceptions("session", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        **d,
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@query_metrics("delete_session")
@pg_query
@beartype
async def delete_session(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> list[tuple[str, list]]:
    """
    Constructs SQL queries to delete a session and its participant lookups.

    Args:
        developer_id (UUID): The developer's UUID
        session_id (UUID): The session's UUID to delete

    Returns:
        list[tuple[str, list]]: List of SQL queries and their parameters
    """
    params = [developer_id, session_id]

    return [
        (lookup_query, params),  # Delete from lookup table first due to FK constraint
        (session_query, params),  # Then delete from sessions table
    ]
