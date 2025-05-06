from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import UpdateUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is provided
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $6
)
UPDATE users
SET
    name = $3, -- name
    about = $4, -- about
    metadata = $5, -- metadata
    project_id = CASE
        WHEN $6 IS NOT NULL THEN (SELECT project_id FROM proj)
        ELSE project_id
    END
WHERE developer_id = $1 -- developer_id
AND user_id = $2 -- user_id
RETURNING
    users.*,
    (SELECT canonical_name FROM projects WHERE project_id = users.project_id) AS project;
"""


@rewrap_exceptions(common_db_exceptions("user", ["update"]))
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
    },
)
@query_metrics("update_user")
@pg_query
@beartype
async def update_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: UpdateUserRequest,
) -> tuple[str, list]:
    """
    Constructs an optimized SQL query to update a user's details.
    Uses primary key for efficient update.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID
        data (UpdateUserRequest): Updated user data

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    # Check if project exists if it's provided
    project_canonical_name = data.project

    if project_canonical_name:
        project_exists_result = await project_exists(developer_id, project_canonical_name)

        if not project_exists_result[0]["project_exists"]:
            raise HTTPException(
                status_code=404, detail=f"Project '{project_canonical_name}' not found"
            )

    params = [
        developer_id,
        user_id,
        data.name,
        data.about,
        data.metadata or {},
        project_canonical_name,
    ]

    return (
        user_query,
        params,
    )
