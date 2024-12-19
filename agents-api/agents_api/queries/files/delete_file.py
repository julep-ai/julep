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

# Simple query to delete file (when no associations exist)
delete_file_query = parse_one("""
DELETE FROM files 
WHERE developer_id = $1 
AND file_id = $2
AND NOT EXISTS (
    SELECT 1 
    FROM user_files uf 
    WHERE uf.file_id = $2
    LIMIT 1
)
AND NOT EXISTS (
    SELECT 1 
    FROM agent_files af 
    WHERE af.file_id = $2
    LIMIT 1
)
RETURNING file_id;
""").sql(pretty=True)

# Query to delete owner's association
delete_user_assoc_query = parse_one("""
DELETE FROM user_files 
WHERE developer_id = $1 
AND file_id = $2 
AND user_id = $3
RETURNING file_id;
""").sql(pretty=True)

delete_agent_assoc_query = parse_one("""
DELETE FROM agent_files 
WHERE developer_id = $1 
AND file_id = $2 
AND agent_id = $3
RETURNING file_id;
""").sql(pretty=True)


# @rewrap_exceptions(
#     {
#         asyncpg.NoDataFoundError: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="File not found",
#         ),
#     }
# )
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
    file_id: UUID,
    developer_id: UUID,
    owner_id: UUID | None = None,
    owner_type: Literal["user", "agent"] | None = None,
) -> list[tuple[str, list] | tuple[str, list, str]]:
    """
    Deletes a file and/or its association using simple, efficient queries.

    If owner details provided:
        1. Deletes the owner's association
        2. Checks for remaining associations
        3. Deletes file if no associations remain
    If no owner details:
        - Deletes file only if it has no associations

    Args:
        file_id (UUID): The UUID of the file to be deleted.
        developer_id (UUID): The UUID of the developer owning the file.
        owner_id (UUID | None): Optional owner ID to verify ownership
        owner_type (str | None): Optional owner type to verify ownership

    Returns:
        list[tuple[str, list] | tuple[str, list, str]]: List of SQL queries, their parameters, and fetch type
    """
    queries = []

    if owner_id and owner_type:
        # Delete specific association
        assoc_params = [developer_id, file_id, owner_id]
        assoc_query = (
            delete_user_assoc_query
            if owner_type == "user"
            else delete_agent_assoc_query
        )
        queries.append((assoc_query, assoc_params))

        # If no associations, delete file
        queries.append((delete_file_query, [developer_id, file_id]))
    else:
        # Try to delete file if it has no associations
        queries.append((delete_file_query, [developer_id, file_id]))

    return queries
