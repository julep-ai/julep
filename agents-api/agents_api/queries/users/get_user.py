from typing import Any
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from psycopg import errors as psycopg_errors
from sqlglot import parse_one

from ...autogen.openapi_model import User
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

@rewrap_exceptions({
    psycopg_errors.ForeignKeyViolation: partialclass(
        HTTPException,
        status_code=404,
        detail="The specified developer does not exist.",
    )
})
@wrap_in_class(User, one=True)
@increase_counter("get_user")
@pg_query
@beartype
def get_user_query(*, developer_id: UUID, user_id: UUID) -> tuple[str, dict]:
    """
    Constructs an optimized SQL query to retrieve a user's details.
    Uses the primary key index (developer_id, user_id) for efficient lookup.

    Args:
        developer_id (UUID): The UUID of the developer.
        user_id (UUID): The UUID of the user to retrieve.

    Returns:
        tuple[str, dict]: SQL query and parameters.
    """
    query = parse_one("""
    SELECT 
        user_id as id,
        developer_id,
        name,
        about,
        metadata,
        created_at,
        updated_at
    FROM users
    WHERE developer_id = %(developer_id)s 
    AND user_id = %(user_id)s;
    """).sql()

    return query, {"developer_id": developer_id, "user_id": user_id}