"""
This module contains the functionality for creating files in the PostgreSQL database.
It includes functions to construct and execute SQL queries for inserting new file records.
"""

import base64
import hashlib
from typing import Any, Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateFileRequest, File
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Create file
file_query = parse_one("""
INSERT INTO files (
    developer_id,
    file_id,
    name,
    description,
    mime_type,
    size,
    hash,
)
VALUES (
    $1, -- developer_id
    $2, -- file_id
    $3, -- name
    $4, -- description
    $5, -- mime_type
    $6, -- size
    $7, -- hash
)
RETURNING *;
""").sql(pretty=True)

# Create user file association
user_file_query = parse_one("""
INSERT INTO user_files (
    developer_id,
    user_id,
    file_id
)
VALUES ($1, $2, $3)
ON CONFLICT (developer_id, user_id, file_id) DO NOTHING;  -- Uses primary key index
""").sql(pretty=True)

# Create agent file association
agent_file_query = parse_one("""
INSERT INTO agent_files (
    developer_id,
    agent_id,
    file_id
)
VALUES ($1, $2, $3)
ON CONFLICT (developer_id, agent_id, file_id) DO NOTHING;  -- Uses primary key index
""").sql(pretty=True)


# Add error handling decorator
# @rewrap_exceptions(
#     {
#         asyncpg.UniqueViolationError: partialclass(
#             HTTPException,
#             status_code=409,
#             detail="A file with this name already exists for this developer",
#         ),
#         asyncpg.NoDataFoundError: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="The specified owner does not exist",
#         ),
#         asyncpg.ForeignKeyViolationError: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="The specified developer does not exist",
#         ),
#     }
# )
@wrap_in_class(
    File,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["file_id"],
        "content": "DUMMY: NEED TO FETCH CONTENT FROM BLOB STORAGE",
    },
)
@increase_counter("create_file")
@pg_query
@beartype
async def create_file(
    *,
    developer_id: UUID,
    file_id: UUID | None = None,
    data: CreateFileRequest,
    owner_type: Literal["user", "agent"] | None = None,
    owner_id: UUID | None = None,
) -> list[tuple[str, list] | tuple[str, list, str]]:
    """
    Constructs and executes SQL queries to create a new file and optionally associate it with an owner.

    Parameters:
        developer_id (UUID): The unique identifier for the developer.
        file_id (UUID | None): Optional unique identifier for the file.
        data (CreateFileRequest): The file data to insert.
        owner_type (Literal["user", "agent"] | None): Optional type of owner
        owner_id (UUID | None): Optional ID of the owner

    Returns:
        list[tuple[str, list] | tuple[str, list, str]]: List of SQL queries, their parameters, and fetch type
    """
    file_id = file_id or uuid7()

    # Calculate size and hash
    content_bytes = base64.b64decode(data.content)
    data.size = len(content_bytes)
    data.hash = hashlib.sha256(content_bytes).digest()

    # Base file parameters
    file_params = [
        developer_id,
        file_id,
        data.name,
        data.description,
        data.mime_type,
        data.size,
        data.hash,
    ]

    queries = []

    # Create the file
    queries.append((file_query, file_params))

    # Create the association only if both owner_type and owner_id are provided
    if owner_type and owner_id:
        assoc_params = [developer_id, owner_id, file_id]
        if owner_type == "user":
            queries.append((user_file_query, assoc_params))
        else:  # agent
            queries.append((agent_file_query, assoc_params))

    return queries
