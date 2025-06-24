from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import PatchUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..sql_builder import build_patch_query
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Base query to check project and get user after update
user_select_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is being updated
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $2
    AND $2 IS NOT NULL
), project_exists AS (
    -- Check if the specified project exists
    SELECT
        CASE
            WHEN $2 IS NULL THEN TRUE -- No project specified, so exists check passes
            WHEN EXISTS (SELECT 1 FROM proj) THEN TRUE -- Project exists
            ELSE FALSE -- Project specified but doesn't exist
        END AS exists
), user_update AS (
    -- UPDATE_PLACEHOLDER
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
        u.user_id
    FROM proj p, user_update u
    ON CONFLICT (project_id, user_id) DO NOTHING
    RETURNING 1
), old_associations AS (
    -- Remove any previous project associations if we're updating with a new project
    DELETE FROM project_users pu
    WHERE pu.developer_id = $1
    AND pu.user_id IN (SELECT user_id FROM user_update)
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
         WHERE pu.developer_id = $1 AND pu.user_id = u.user_id
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
async def patch_user_query(
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
    # Prepare patch data
    patch_fields = {
        "name": data.name,
        "about": data.about,
    }

    # Handle metadata separately (merge operation)
    if data.metadata is not None:
        patch_fields["metadata"] = data.metadata

    # Filter out None values
    update_fields = {k: v for k, v in patch_fields.items() if v is not None}

    # If no fields to update, just return the user
    if not update_fields:
        simple_select = """
        SELECT
            u.*,
            COALESCE(
                (SELECT canonical_name
                 FROM projects p
                 JOIN project_users pu ON p.project_id = pu.project_id
                 WHERE pu.developer_id = $1 AND pu.user_id = $2
                 LIMIT 1),
                'default'
            ) AS project
        FROM users u
        WHERE u.user_id = $2 AND u.developer_id = $1;
        """
        return (simple_select, [str(developer_id), str(user_id)])

    # Build the UPDATE query
    # Note: We already have 2 parameters in the outer query ($1 and $2), so start from 3
    update_query, update_params = build_patch_query(
        table_name="users",
        patch_data=update_fields,
        where_conditions={"user_id": str(user_id), "developer_id": str(developer_id)},
        returning_fields=["*"],
        param_offset=2,  # Start from $3 since $1 and $2 are used in the CTE
    )

    # Special handling for metadata - use JSONB merge
    if data.metadata is not None:
        # Find metadata in update query and modify it to use merge operator
        update_query = update_query.replace(
            '"metadata" = $', '"metadata" = "metadata" || $'
        )

    # Replace the UPDATE_PLACEHOLDER in the main query
    final_query = user_select_query.replace("-- UPDATE_PLACEHOLDER", update_query)

    # Combine parameters: developer_id, project_name, then update params
    all_params = [str(developer_id), data.project or "default", *update_params]

    return (final_query, all_params)


async def patch_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: PatchUserRequest,
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

    return await patch_user_query(
        developer_id=developer_id,
        user_id=user_id,
        data=data,
        connection_pool=connection_pool,
    )
