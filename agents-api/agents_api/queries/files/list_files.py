"""
This module contains the functionality for listing files from the PostgreSQL database.
It constructs and executes SQL queries to fetch a list of files based on developer ID with pagination.
"""

from typing import Annotated, Literal
from uuid import UUID

from beartype import beartype
from beartype.vale import Is

from ...autogen.openapi_model import File
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import make_num_validator, pg_query, rewrap_exceptions, wrap_in_class

# Base query for listing files
base_files_query = """
SELECT f.*
FROM files f
LEFT JOIN file_owners fo ON f.developer_id = fo.developer_id AND f.file_id = fo.file_id
WHERE f.developer_id = $1
"""


@rewrap_exceptions(common_db_exceptions("file", ["list"]))
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
    limit: Annotated[
        int,
        Is[
            make_num_validator(
                min_value=1, max_value=100, err_msg="Limit must be between 1 and 100"
            )
        ],
    ] = 100,
    offset: Annotated[
        int, Is[make_num_validator(min_value=0, err_msg="Offset must be >= 0")]
    ] = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, list]:
    """
    Lists files with optional owner filtering, pagination, and sorting.
    """
    # Validate parameters
    # if direction.lower() not in ["asc", "desc"]:
    #     raise HTTPException(status_code=400, detail="Invalid sort direction")

    # if sort_by not in ["created_at", "updated_at"]:
    #     raise HTTPException(status_code=400, detail="Invalid sort field")

    # Start with the base query
    query = base_files_query
    params = [developer_id]

    # Add owner filtering
    if owner_type and owner_id:
        query += " AND fo.owner_type = $2 AND fo.owner_id = $3"
        params.extend([owner_type, owner_id])

    # Add sorting and pagination
    query += (
        f" ORDER BY {sort_by} {direction} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    )
    params.extend([limit, offset])

    return query, params
