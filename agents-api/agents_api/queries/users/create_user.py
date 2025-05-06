from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
WITH new_user AS (
    INSERT INTO users (
        developer_id,
        user_id,
        name,
        about,
        metadata
    )
    VALUES (
        $1, -- developer_id
        $2, -- user_id
        $3, -- name
        $4, -- about
        $5::jsonb -- metadata
    )
    RETURNING *
), proj AS (
    -- Find project ID by canonical name
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $6
), project_association AS (
    -- Update user with project_id
    UPDATE users
    SET project_id = p.project_id
    FROM proj p
    WHERE users.user_id = $2 AND users.developer_id = $1
    RETURNING 1
)
SELECT
    u.*,
    p.canonical_name AS project
FROM new_user u
LEFT JOIN proj p ON TRUE;
"""


@rewrap_exceptions(common_db_exceptions("user", ["create"]))
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
    },
)
@query_metrics("create_user")
@pg_query
@beartype
async def create_user(
    *,
    developer_id: UUID,
    user_id: UUID | None = None,
    data: CreateUserRequest,
) -> tuple[str, list]:
    """
    Constructs the SQL query to create a new user.

    Args:
        developer_id (UUID): The UUID of the developer creating the user.
        user_id (UUID, optional): The UUID for the new user. If None, one will be generated.
        data (CreateUserRequest): The user data to insert.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.
    """
    user_id = user_id or uuid7()
    metadata = data.metadata or {}

    # Get project (default if not specified)
    project_canonical_name = data.project

    # Check if the project exists
    project_exists_result = await project_exists(developer_id, project_canonical_name)

    if not project_exists_result[0]["project_exists"]:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_canonical_name}' not found"
        )

    params = [
        developer_id,  # $1
        user_id,  # $2
        data.name,  # $3
        data.about,  # $4
        metadata,  # $5
        project_canonical_name,  # $6
    ]

    return (
        user_query,
        params,
    )
