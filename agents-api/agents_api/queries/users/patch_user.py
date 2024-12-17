from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import PatchUserRequest, ResourceUpdatedResponse
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
raw_query = """
UPDATE users
SET 
    name = CASE 
        WHEN $3::text IS NOT NULL THEN $3 
        ELSE name 
    END,
    about = CASE 
        WHEN $4::text IS NOT NULL THEN $4 
        ELSE about 
    END,
    metadata = CASE 
        WHEN $5::jsonb IS NOT NULL THEN metadata || $5 
        ELSE metadata 
    END
WHERE developer_id = $1 
AND user_id = $2
RETURNING 
    user_id as id,
    developer_id,
    name,
    about,
    metadata,
    created_at,
    updated_at;
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
@wrap_in_class(ResourceUpdatedResponse, one=True)
@increase_counter("patch_user")
@pg_query
@beartype
async def patch_user(
    *, developer_id: UUID, user_id: UUID, data: PatchUserRequest
) -> tuple[str, list]:
    """
    Constructs an optimized SQL query for partial user updates.
    Uses primary key for efficient update and jsonb_merge for metadata.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID
        data (PatchUserRequest): Partial update data

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    params = [
        developer_id,
        user_id,
        data.name,  # Will be NULL if not provided
        data.about,  # Will be NULL if not provided
        data.metadata,  # Will be NULL if not provided
    ]

    return query, params
