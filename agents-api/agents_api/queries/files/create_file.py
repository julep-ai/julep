"""
This module contains the functionality for creating files in the PostgreSQL database.
It includes functions to construct and execute SQL queries for inserting new file records.
"""

import base64
import hashlib
from typing import Literal
from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateFileRequest, File
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Create file
file_query = """
INSERT INTO files (
    developer_id,
    file_id,
    name,
    description,
    mime_type,
    size,
    hash
)
VALUES (
    $1, -- developer_id
    $2, -- file_id
    $3, -- name
    $4, -- description
    $5, -- mime_type
    $6, -- size
    $7  -- hash
)
RETURNING *;
"""

# Replace both user_file and agent_file queries with a single file_owner query
file_owner_query = """
WITH inserted_owner AS (
    INSERT INTO file_owners (
        developer_id,
        file_id,
        owner_type,
        owner_id
    )
    VALUES ($1, $2, $3, $4)
    RETURNING file_id
)
SELECT f.*
FROM inserted_owner io
JOIN files f ON f.file_id = io.file_id;
"""


# Add error handling decorator
@rewrap_exceptions(common_db_exceptions("file", ["create"]))
@wrap_in_class(
    File,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["file_id"],
        "hash": d["hash"].hex(),
        "content": "DUMMY: NEED TO FETCH CONTENT FROM BLOB STORAGE",
    },
)
@query_metrics("create_file")
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
    size = len(content_bytes)
    hash_bytes = hashlib.sha256(content_bytes).digest()

    # Base file parameters
    file_params = [
        developer_id,
        file_id,
        data.name,
        data.description,
        data.mime_type,
        size,
        hash_bytes,
    ]

    queries = []

    # Create the file first
    queries.append((file_query, file_params))

    # Then create the association if owner info provided
    if owner_type and owner_id:
        assoc_params = [developer_id, file_id, owner_type, owner_id]
        queries.append((file_owner_query, assoc_params))

    return queries
