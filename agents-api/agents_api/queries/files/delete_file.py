"""
This module contains the functionality for deleting files from the PostgreSQL database.
It constructs and executes SQL queries to remove file records and associated data.
"""

from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Delete file query with ownership check
delete_file_query = parse_one("""
WITH deleted_owners AS (
    DELETE FROM file_owners
    WHERE developer_id = $1 
    AND file_id = $2
    AND (
        ($3::text IS NULL AND $4::uuid IS NULL) OR
        (owner_type = $3 AND owner_id = $4)
    )
)
DELETE FROM files 
WHERE developer_id = $1 
AND file_id = $2
AND ($3::text IS NULL OR EXISTS (
    SELECT 1 FROM file_owners 
    WHERE developer_id = $1 
    AND file_id = $2 
    AND owner_type = $3 
    AND owner_id = $4
))
RETURNING file_id;
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
            detail="The specified developer or owner does not exist",
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["file_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@increase_counter("delete_file")
@pg_query
@beartype
async def delete_file(
    *,
    developer_id: UUID,
    file_id: UUID,
    owner_type: Literal["user", "agent"] | None = None,
    owner_id: UUID | None = None,
) -> tuple[str, list]:
    """
    Deletes a file and its ownership records.

    Args:
        developer_id: The developer's UUID
        file_id: The file's UUID
        owner_type: Optional type of owner ("user" or "agent")
        owner_id: Optional UUID of the owner

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    return (
        delete_file_query,
        [developer_id, file_id, owner_type, owner_id],
    )
