from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import CreateOrUpdateUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating or updating a user
user_query = """
WITH proj AS (
    -- Find project ID by canonical name
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $6
)
INSERT INTO users (
    developer_id,
    user_id,
    name,
    about,
    metadata,
    project_id
)
VALUES (
    $1, -- developer_id
    $2, -- user_id
    $3, -- name
    $4, -- about
    $5::jsonb, -- metadata
    (SELECT project_id FROM proj) -- project_id
)
ON CONFLICT (developer_id, user_id) DO UPDATE SET
    name = EXCLUDED.name,
    about = EXCLUDED.about,
    metadata = EXCLUDED.metadata,
    project_id = (SELECT project_id FROM proj)
RETURNING
    users.*,
    (SELECT canonical_name FROM proj) AS project;
"""


@rewrap_exceptions(common_db_exceptions("user", ["create_or_update"]))
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
    },
)
@query_metrics("create_or_update_user")
@pg_query
@beartype
async def create_or_update_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: CreateOrUpdateUserRequest,
) -> tuple[str, list]:
    """
    Constructs an SQL query to create or update a user.

    Args:
        developer_id (UUID): The UUID of the developer.
        user_id (UUID): The UUID of the user.
        data (CreateOrUpdateUserRequest): The user data to insert or update.

    Returns:
        tuple[str, list]: SQL query and parameters.

    Raises:
        HTTPException: If developer doesn't exist (404) or on unique constraint violation (409)
    """
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
        data.metadata or {},  # $5
        project_canonical_name,  # $6
    ]

    return (
        user_query,
        params,
    )
