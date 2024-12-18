from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import User
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
raw_query = """
SELECT 
    user_id as id,
    developer_id,
    name,
    about,
    metadata,
    created_at,
    updated_at
FROM users
WHERE developer_id = $1 
AND user_id = $2;
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
@wrap_in_class(User, one=True)
@increase_counter("get_user")
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
        query,
        [developer_id, user_id],
    )
