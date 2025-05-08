from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import PatchUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is being updated
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $6
    AND $6 IS NOT NULL
), project_exists AS (
    -- Check if the specified project exists
    SELECT
        CASE
            WHEN $6 IS NULL THEN TRUE -- No project specified, so exists check passes
            WHEN EXISTS (SELECT 1 FROM proj) THEN TRUE -- Project exists
            ELSE FALSE -- Project specified but doesn't exist
        END AS exists
), user_update AS (
    -- Only proceed with update if project exists
    UPDATE users
    SET
        name = CASE
            WHEN $3::text IS NOT NULL THEN $3 -- name
            ELSE name
        END,
        about = CASE
            WHEN $4::text IS NOT NULL THEN $4 -- about
            ELSE about
        END,
        metadata = CASE
            WHEN $5::jsonb IS NOT NULL THEN metadata || $5 -- metadata
            ELSE metadata
        END
    WHERE developer_id = $1
    AND user_id = $2
    AND (SELECT exists FROM project_exists)
    RETURNING *
), project_association AS (
    -- Create or update project association if project is being updated
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
    (SELECT exists FROM project_exists) AS project_exists,
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


@rewrap_exceptions(common_db_exceptions("user", ["patch"]))
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
    },
)
@query_metrics("patch_user")
@pg_query
@beartype
async def patch_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: PatchUserRequest,
) -> tuple[str, list]:
    """
    Constructs an optimized SQL query for partial user updates.
    Uses primary key for efficient update and jsonb_merge for metadata.
    Includes project existence check directly in the SQL.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID
        data (PatchUserRequest): Partial update data

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    # SQL will return project_exists status in the result
    # If false, the row won't be updated, and we'll raise an appropriate exception
    # in the error handling layer
    params = [
        developer_id,  # $1
        user_id,  # $2
        data.name,  # $3. Will be NULL if not provided
        data.about,  # $4. Will be NULL if not provided
        data.metadata,  # $5. Will be NULL if not provided
        data.project or "default",  # $6. Use default if None is provided
    ]

    return (
        user_query,
        params,
    )
