from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import ResourceDeletedResponse
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
raw_query = """
WITH deleted_data AS (
    DELETE FROM user_files 
    WHERE developer_id = $1 AND user_id = $2
),
deleted_docs AS (
    DELETE FROM user_docs 
    WHERE developer_id = $1 AND user_id = $2
)
DELETE FROM users 
WHERE developer_id = $1 AND user_id = $2
RETURNING user_id as id, developer_id;
"""

# Parse and optimize the query
query = optimize(
    parse_one(raw_query),
    schema={
        "user_files": {"developer_id": "UUID", "user_id": "UUID"},
        "user_docs": {"developer_id": "UUID", "user_id": "UUID"},
        "users": {"developer_id": "UUID", "user_id": "UUID"},
    },
).sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        )
    }
)
@wrap_in_class(ResourceDeletedResponse, one=True)
@increase_counter("delete_user")
@pg_query
@beartype
def delete_user(*, developer_id: UUID, user_id: UUID) -> tuple[str, list]:
    """
    Constructs optimized SQL query to delete a user and related data.
    Uses primary key for efficient deletion.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID

    Returns:
        tuple[str, list]: SQL query and parameters
    """

    return (
        query,
        [developer_id, user_id],
    )
