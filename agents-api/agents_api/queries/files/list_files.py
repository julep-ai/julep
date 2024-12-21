"""
This module contains the functionality for listing files from the PostgreSQL database.
It constructs and executes SQL queries to fetch a list of files based on developer ID with pagination.
"""

from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import File
from ..utils import pg_query, wrap_in_class

# Query to list all files for a developer (uses developer_id index)
developer_files_query = parse_one("""
SELECT f.*
FROM files f
LEFT JOIN file_owners fo ON f.developer_id = fo.developer_id AND f.file_id = fo.file_id
WHERE f.developer_id = $1
ORDER BY 
    CASE 
        WHEN $4 = 'created_at' AND $5 = 'asc' THEN created_at 
        WHEN $4 = 'created_at' AND $5 = 'desc' THEN created_at 
        WHEN $4 = 'updated_at' AND $5 = 'asc' THEN updated_at
        WHEN $4 = 'updated_at' AND $5 = 'desc' THEN updated_at
    END DESC NULLS LAST
LIMIT $2 
OFFSET $3;
""").sql(pretty=True)

# Query to list files for a specific owner (uses composite indexes)
owner_files_query = parse_one("""
SELECT f.*
FROM files f
JOIN file_owners fo ON f.developer_id = fo.developer_id AND f.file_id = fo.file_id
WHERE fo.developer_id = $1 
AND fo.owner_id = $6
AND fo.owner_type = $7
ORDER BY 
    CASE 
        WHEN $4 = 'created_at' AND $5 = 'asc' THEN created_at 
        WHEN $4 = 'created_at' AND $5 = 'desc' THEN created_at 
        WHEN $4 = 'updated_at' AND $5 = 'asc' THEN updated_at
        WHEN $4 = 'updated_at' AND $5 = 'desc' THEN updated_at
    END DESC NULLS LAST
LIMIT $2 
OFFSET $3;
""").sql(pretty=True)


@wrap_in_class(
    File,
    one=False,
    transform=lambda d: {
        **d,
        "id": d["file_id"],
        "hash": d["hash"].hex(),
        "content": "DUMMY: NEED TO FETCH CONTENT FROM BLOB STORAGE",
    },
)
@pg_query
@beartype
async def list_files(
    *,
    developer_id: UUID,
    owner_id: UUID | None = None,
    owner_type: Literal["user", "agent"] | None = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, list]:
    """
    Lists files with optimized queries for two cases:
    1. Owner specified: Returns files associated with that owner
    2. No owner: Returns all files for the developer

    Args:
        developer_id: UUID of the developer
        owner_id: Optional UUID of the owner (user or agent)
        owner_type: Optional type of owner ("user" or "agent")
        limit: Maximum number of records to return (1-100)
        offset: Number of records to skip
        sort_by: Field to sort by
        direction: Sort direction ('asc' or 'desc')

    Returns:
        Tuple of (query, params)

    Raises:
        HTTPException: If parameters are invalid
    """
    # Validate parameters
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if limit > 100 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    # Base parameters used in all queries
    params = [
        developer_id,
        limit,
        offset,
        sort_by,
        direction,
    ]

    # Choose appropriate query based on owner details
    if owner_id and owner_type:
        params.extend([owner_id, owner_type])  # Add owner_id as $6 and owner_type as $7
        query = owner_files_query  # Use single query with owner_type parameter
    else:
        query = developer_files_query

    return (query, params)
