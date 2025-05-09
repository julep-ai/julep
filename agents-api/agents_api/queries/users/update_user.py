from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import UpdateUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is provided
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $6
    AND $6 IS NOT NULL
), user_update AS (
    -- Update the user details
    UPDATE users
    SET
        name = $3, -- name
        about = $4, -- about
        metadata = $5 -- metadata
    WHERE developer_id = $1 -- developer_id
    AND user_id = $2 -- user_id
    RETURNING *
), project_association AS (
    -- Create or update project association if project is provided and exists
    INSERT INTO project_users (
        project_id,
        developer_id,
        user_id
    )
    SELECT
        p.project_id,
        $1,
        $2
    FROM proj p
    ON CONFLICT (project_id, user_id) DO NOTHING
    RETURNING 1
), old_associations AS (
    -- Remove any previous project associations if we're updating with a new project
    DELETE FROM project_users pu
    WHERE pu.developer_id = $1
    AND pu.user_id = $2
    AND EXISTS (SELECT 1 FROM proj) -- Only delete if we have a new project
    AND NOT EXISTS (
        SELECT 1 FROM proj p
        WHERE p.project_id = pu.project_id
    )
)
SELECT
    u.*,
    COALESCE(
        (SELECT canonical_name FROM proj),
        (SELECT canonical_name
         FROM projects p
         JOIN project_users pu ON p.project_id = pu.project_id
         WHERE pu.developer_id = $1 AND pu.user_id = $2
         LIMIT 1),
        'default'
    ) AS project
FROM user_update u;
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

    params = [
        developer_id,
        user_id,
        data.name,
        data.about,
        data.metadata or {},
        data.project or "default",
    ]

    return (
        user_query,
        params,
    )
