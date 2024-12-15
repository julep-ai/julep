from typing import Any
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from psycopg import errors as psycopg_errors
from sqlglot import parse_one

from ...autogen.openapi_model import UpdateUserRequest, ResourceUpdatedResponse
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

@rewrap_exceptions({
    psycopg_errors.ForeignKeyViolation: partialclass(
        HTTPException,
        status_code=404,
        detail="The specified developer does not exist.",
    )
})
@wrap_in_class(ResourceUpdatedResponse, one=True)
@increase_counter("update_user")
@pg_query
@beartype
def update_user_query(
    *, 
    developer_id: UUID, 
    user_id: UUID, 
    data: UpdateUserRequest
) -> tuple[str, dict]:
    """
    Constructs an optimized SQL query to update a user's details.
    Uses primary key for efficient update.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID
        data (UpdateUserRequest): Updated user data

    Returns:
        tuple[str, dict]: SQL query and parameters
    """
    query = parse_one("""
    UPDATE users
    SET 
        name = %(name)s,
        about = %(about)s,
        metadata = %(metadata)s
    WHERE developer_id = %(developer_id)s 
    AND user_id = %(user_id)s
    RETURNING 
        user_id as id,
        developer_id,
        name,
        about,
        metadata,
        created_at,
        updated_at;
    """).sql()

    params = {
        "developer_id": developer_id,
        "user_id": user_id,
        "name": data.name,
        "about": data.about,
        "metadata": data.metadata or {},
    }

    return query, params