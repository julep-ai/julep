from uuid import UUID

import asyncpg
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
), user_op AS (
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
    ON CONFLICT (developer_id, user_id) DO UPDATE SET
        name = EXCLUDED.name,
        about = EXCLUDED.about,
        metadata = EXCLUDED.metadata
    RETURNING *
), project_association AS (
    -- Create or update project association
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
    WHERE p.project_id IS NOT NULL
    ON CONFLICT (project_id, user_id) DO NOTHING
    RETURNING 1
)
SELECT
    u.*,
    p.canonical_name AS project
FROM user_op u
LEFT JOIN proj p ON TRUE;
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
async def create_or_update_user_query(
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

    params = [
        developer_id,  # $1
        user_id,  # $2
        data.name,  # $3
        data.about,  # $4
        data.metadata or {},  # $5
        data.project or "default",  # $6
    ]

    return (
        user_query,
        params,
    )


async def create_or_update_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: CreateOrUpdateUserRequest,
    connection_pool: asyncpg.Pool | None = None,
) -> User:
    # Get project (default if not specified)
    project_canonical_name = data.project or "default"

    # Check if the project exists
    project_exists_result = await project_exists(
        developer_id, project_canonical_name, connection_pool=connection_pool
    )

    if not project_exists_result[0]["project_exists"]:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_canonical_name}' not found"
        )

    return await create_or_update_user_query(
        developer_id=developer_id,
        user_id=user_id,
        data=data,
        connection_pool=connection_pool,
    )
