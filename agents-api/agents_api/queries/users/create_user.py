from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...metrics.counters import increase_counter
from ...autogen.openapi_model import CreateUserRequest, User
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
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
RETURNING *;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.NullValueNoIndicatorParameterError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
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
@increase_counter("create_user")
@pg_query
@beartype
async def create_user(
    *,
    developer_id: UUID,
    user_id: UUID | None = None,
    data: CreateUserRequest,
) -> tuple[str, list]:
    """
    Constructs the SQL query to create a new user.

    Args:
        developer_id (UUID): The UUID of the developer creating the user.
        user_id (UUID, optional): The UUID for the new user. If None, one will be generated.
        data (CreateUserRequest): The user data to insert.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.
    """
    user_id = user_id or uuid7()

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
