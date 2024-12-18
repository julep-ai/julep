from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import User
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = parse_one("""
SELECT 
    user_id as id, -- user_id
    developer_id, -- developer_id
    name, -- name
    about, -- about
    metadata, -- metadata
    created_at, -- created_at
    updated_at -- updated_at
FROM users
WHERE developer_id = $1 
AND user_id = $2;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified user does not exist.",
        ),
    }
)
@wrap_in_class(User, one=True)
@pg_query
@beartype
async def get_user(*, developer_id: UUID, user_id: UUID) -> tuple[str, list]:
    """
    Constructs an optimized SQL query to retrieve a user's details.
    Uses the primary key index (developer_id, user_id) for efficient lookup.

    Args:
        developer_id (UUID): The UUID of the developer.
        user_id (UUID): The UUID of the user to retrieve.

    Returns:
        tuple[str, list]: SQL query and parameters.
    """

    return (
        user_query,
        [developer_id, user_id],
    )
