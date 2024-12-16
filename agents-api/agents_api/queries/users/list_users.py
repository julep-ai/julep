from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import optimize, parse_one

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
WHERE developer_id = %(developer_id)s
    {metadata_clause}
    AND deleted_at IS NULL
ORDER BY {sort_by} {direction} NULLS LAST
LIMIT %(limit)s 
OFFSET %(offset)s;
"""

# Parse and optimize the query
query_template = optimize(
    parse_one(raw_query),
    schema={
        "users": {
            "developer_id": "UUID",
            "user_id": "UUID",
            "name": "STRING",
            "about": "STRING",
            "metadata": "JSONB",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
        }
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
@wrap_in_class(User)
@increase_counter("list_users")
@pg_query
@beartype
def list_users(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict | None = None,
) -> tuple[str, dict]:
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
        tuple[str, dict]: SQL query and parameters
    """
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    metadata_clause = ""
    params = {"developer_id": developer_id, "limit": limit, "offset": offset}

    if metadata_filter:
        metadata_clause = "AND metadata @> %(metadata_filter)s"
        params["metadata_filter"] = metadata_filter

    query = query_template.format(
        metadata_clause=metadata_clause, sort_by=sort_by, direction=direction
    )

    return query, params
