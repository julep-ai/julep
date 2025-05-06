from typing import Annotated, Literal
from uuid import UUID

from beartype import beartype
from beartype.vale import Is

from ...autogen.openapi_model import User
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import make_num_validator, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
WITH filtered_users AS (
    SELECT
        u.user_id as id, -- user_id
        u.developer_id, -- developer_id
        u.name, -- name
        u.about, -- about
        u.metadata, -- metadata
        u.created_at, -- created_at
        u.updated_at, -- updated_at
        p.canonical_name AS project -- project
    FROM users u
    LEFT JOIN projects p ON u.project_id = p.project_id
    WHERE u.developer_id = $1
        AND ($4::jsonb IS NULL OR u.metadata @> $4)
        AND ($7::text IS NULL OR p.canonical_name = $7)
)
SELECT *
FROM filtered_users
ORDER BY
    CASE WHEN $5 = 'created_at' AND $6 = 'asc' THEN created_at END ASC NULLS LAST,
    CASE WHEN $5 = 'created_at' AND $6 = 'desc' THEN created_at END DESC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'asc' THEN updated_at END ASC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'desc' THEN updated_at END DESC NULLS LAST
LIMIT $2
OFFSET $3;
"""


@rewrap_exceptions(common_db_exceptions("user", ["list"]))
@wrap_in_class(User)
@pg_query
@beartype
async def list_users(
    *,
    developer_id: UUID,
    limit: Annotated[
        int,
        Is[
            make_num_validator(
                min_value=1, max_value=100, err_msg="Limit must be between 1 and 100"
            )
        ],
    ] = 100,
    offset: Annotated[
        int, Is[make_num_validator(min_value=0, err_msg="Offset must be non-negative")]
    ] = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict | None = None,
    project: str | None = None,
) -> tuple[str, list]:
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
        project (str, optional): Filter users by project canonical name

    Returns:
        tuple[str, list]: SQL query and parameters
    """

    params = [
        developer_id,  # $1
        limit,  # $2
        offset,  # $3
        metadata_filter,  # Will be NULL if not provided
        sort_by,  # $5
        direction,  # $6
        project,  # $7
    ]

    return (
        user_query,
        params,
    )
