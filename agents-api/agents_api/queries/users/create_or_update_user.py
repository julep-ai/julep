from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...metrics.counters import increase_counter
from ...autogen.openapi_model import CreateOrUpdateUserRequest, User
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating or updating a user
user_query = parse_one("""
INSERT INTO users (
    developer_id,
    user_id,
    name,
    about,
    metadata
)
VALUES (
    $1, -- developer_id
    $2, -- user_id
    $3, -- name
    $4, -- about
    $5::jsonb -- metadata
)
ON CONFLICT (developer_id, user_id) DO UPDATE SET
    name = EXCLUDED.name,
    about = EXCLUDED.about,
    metadata = EXCLUDED.metadata
RETURNING *;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(  # Add handling for potential race conditions
            HTTPException,
            status_code=409,
            detail="A user with this ID already exists.",
        ),
    }
)
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
    },
)
@increase_counter("create_or_update_user")
@pg_query
@beartype
async def create_or_update_user(
    *, developer_id: UUID, user_id: UUID, data: CreateOrUpdateUserRequest
) -> tuple[str, list]:
    """
    Constructs an SQL query to create or update a user.

    Args:
        developer_id (UUID): The UUID of the developer.
        user_id (UUID): The UUID of the user.
        data (CreateOrUpdateUserRequest): The user data to insert or update.

    Returns:
        tuple[str, list]: SQL query and parameters.

    Raises:
        HTTPException: If developer doesn't exist (404) or on unique constraint violation (409)
    """
    params = [
        developer_id,  # $1
        user_id,  # $2
        data.name,  # $3
        data.about,  # $4
        data.metadata or {},  # $5
    ]

    return (
        user_query,
        params,
    )
