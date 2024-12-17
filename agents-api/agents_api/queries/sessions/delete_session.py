"""This module contains the implementation for deleting sessions from the PostgreSQL database."""

from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL queries
lookup_query = parse_one("""
DELETE FROM session_lookup
WHERE developer_id = $1 AND session_id = $2;
""").sql(pretty=True)

session_query = parse_one("""
DELETE FROM sessions
WHERE developer_id = $1 AND session_id = $2
RETURNING session_id;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["session_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@increase_counter("delete_session")
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
