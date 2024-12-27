"""
This module contains the functionality for retrieving a single file from the PostgreSQL database.
It constructs and executes SQL queries to fetch file details based on file ID and developer ID.
"""

from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import File
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
file_query = """
SELECT f.*
FROM files f
LEFT JOIN file_owners fo ON f.developer_id = fo.developer_id AND f.file_id = fo.file_id
WHERE f.developer_id = $1
AND f.file_id = $2
AND (
    ($3::text IS NULL AND $4::uuid IS NULL) OR
    (fo.owner_type = $3 AND fo.owner_id = $4)
)
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("file", ["get"]))
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
@pg_query
@beartype
async def get_file(
    *,
    file_id: UUID,
    developer_id: UUID,
    owner_type: Literal["user", "agent"] | None = None,
    owner_id: UUID | None = None,
) -> tuple[str, list, Literal["fetchrow", "fetchmany", "fetch"]]:
    """
    Constructs the SQL query to retrieve a file's details.
    Uses composite index on (developer_id, file_id) for efficient lookup.

    Args:
        file_id: The UUID of the file to retrieve
        developer_id: The UUID of the developer owning the file
        owner_type: Optional type of owner ("user" or "agent")
        owner_id: Optional UUID of the owner

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    return (
        file_query,
        [developer_id, file_id, owner_type, owner_id],
        "fetchrow",
    )
