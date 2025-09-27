from uuid import UUID

import asyncpg
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
        name = $3, -- name
        about = $4, -- about
        metadata = $5 -- metadata
    WHERE developer_id = $1 -- developer_id
    AND user_id = $2 -- user_id
    AND (SELECT exists FROM project_exists)
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
async def update_user_query(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: UpdateUserRequest,
) -> tuple[str, list]:
    """
    Constructs an optimized SQL query to update a user's details.
    Uses primary key for efficient update.
    Includes project existence check directly in the SQL.

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


async def update_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: UpdateUserRequest,
    connection_pool: asyncpg.Pool | None = None,
) -> User:
    project_canonical_name = data.project or "default"
    project_exists_result = await project_exists(
        developer_id, project_canonical_name, connection_pool=connection_pool
    )

    if not project_exists_result[0]["project_exists"]:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_canonical_name}' not found"
        )

    return await update_user_query(
        developer_id=developer_id,
        user_id=user_id,
        data=data,
        connection_pool=connection_pool,
    )
