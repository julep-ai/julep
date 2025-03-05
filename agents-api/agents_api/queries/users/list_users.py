from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import User
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
WITH filtered_users AS (
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
        AND ($4::jsonb IS NULL OR metadata @> $4)
)
SELECT *
FROM filtered_users
ORDER BY
    CASE WHEN $5 = 'created_at' AND $6 = 'asc' THEN created_at END ASC NULLS LAST,
    CASE WHEN $5 = 'created_at' AND $6 = 'desc' THEN created_at END DESC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'asc' THEN updated_at END ASC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'desc' THEN updated_at END DESC NULLS LAST
LIMIT $2
OFFSET $3;
"""


@rewrap_exceptions(common_db_exceptions("user", ["list"]))
@wrap_in_class(User)
@pg_query
@beartype
async def list_users(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict | None = None,
) -> tuple[str, list]:
    """
    Constructs an optimized SQL query for listing users with pagination and filtering.
    Uses indexes on developer_id and metadata for efficient querying.

    Args:
        developer_id (UUID): The developer's UUID
        limit (int): Maximum number of records to return
        offset (int): Number of records to skip
        sort_by (str): Field to sort by
        direction (str): Sort direction
        metadata_filter (dict, optional): Metadata-based filters

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    # Validate parameters
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if sort_by not in ["created_at", "updated_at"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    params = [
        developer_id,  # $1
        limit,  # $2
        offset,  # $3
        metadata_filter,  # Will be NULL if not provided
        sort_by,  # $4
        direction,  # $5
    ]

    return (
        user_query,
        params,
    )
