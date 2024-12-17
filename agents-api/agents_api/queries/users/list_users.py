from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import User
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
raw_query = """
WITH filtered_users AS (
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


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        )
    }
)
@wrap_in_class(User)
@increase_counter("list_users")
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
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    params = [
        developer_id,
        limit,
        offset,
        metadata_filter,  # Will be NULL if not provided
        sort_by,
        direction,
    ]

    return (
        raw_query,
        params,
    )
