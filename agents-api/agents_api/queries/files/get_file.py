"""
This module contains the functionality for retrieving a single file from the PostgreSQL database.
It constructs and executes SQL queries to fetch file details based on file ID and developer ID.
"""

from uuid import UUID

from beartype import beartype
from sqlglot import parse_one
from fastapi import HTTPException
import asyncpg

from ...autogen.openapi_model import File
from ..utils import pg_query, rewrap_exceptions, wrap_in_class, partialclass

# Define the raw SQL query
file_query = parse_one("""
SELECT 
    file_id,      -- Only select needed columns
    developer_id,
    name,
    description,
    mime_type,
    size,
    hash,
    created_at,
    updated_at
FROM files
WHERE developer_id = $1  -- Order matches composite index (developer_id, file_id)
  AND file_id = $2      -- Using both parts of the index
LIMIT 1;                -- Early termination once found
""").sql(pretty=True)

@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="File not found",
        ),
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="Developer not found",
        ),
    }
)
@wrap_in_class(File, one=True, transform=lambda d: {"id": d["file_id"], **d})
@pg_query
@beartype
async def get_file(*, file_id: UUID, developer_id: UUID) -> tuple[str, list]:
    """
    Constructs the SQL query to retrieve a file's details.
    Uses composite index on (developer_id, file_id) for efficient lookup.

    Args:
        file_id (UUID): The UUID of the file to retrieve.
        developer_id (UUID): The UUID of the developer owning the file.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.

    Raises:
        HTTPException: If file or developer not found (404)
    """
    return (
        file_query,
        [developer_id, file_id],  # Order matches index columns
    ) 