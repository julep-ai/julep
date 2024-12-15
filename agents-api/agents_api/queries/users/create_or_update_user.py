from typing import Any
from uuid import UUID

from asyncpg import exceptions as asyncpg_exceptions
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import CreateUserRequest, User
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class


@rewrap_exceptions(
    {
        asyncpg_exceptions.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        )
    }
)
@wrap_in_class(User)
@increase_counter("create_or_update_user")
@pg_query
@beartype
def create_or_update_user_query(
    *, developer_id: UUID, user_id: UUID, data: CreateUserRequest
) -> tuple[str, dict]:
    """
    Constructs an SQL query to create or update a user.

    Args:
        developer_id (UUID): The UUID of the developer.
        user_id (UUID): The UUID of the user.
        data (CreateUserRequest): The user data to insert or update.

    Returns:
        tuple[str, dict]: SQL query and parameters.
    """
    query = parse_one("""
    INSERT INTO users (
        developer_id,
        user_id,
        name,
        about,
        metadata
    )
    VALUES (
        %(developer_id)s,
        %(user_id)s,
        %(name)s,
        %(about)s,
        %(metadata)s
    )
    ON CONFLICT (developer_id, user_id) DO UPDATE SET
        name = EXCLUDED.name,
        about = EXCLUDED.about,
        metadata = EXCLUDED.metadata
    RETURNING *;
    """).sql()

    params = {
        "developer_id": developer_id,
        "user_id": user_id,
        "name": data.name,
        "about": data.about,
        "metadata": data.metadata or {},
    }

    return query, params
