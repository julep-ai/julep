from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import PatchUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is being updated
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $6
    AND $6 IS NOT NULL
)
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
    END,
    project_id = CASE
        WHEN $6 IS NOT NULL THEN (SELECT project_id FROM proj)
        ELSE project_id
    END
WHERE developer_id = $1
AND user_id = $2
RETURNING
    users.*,
    (SELECT canonical_name FROM projects WHERE project_id = users.project_id) AS project;
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

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID
        data (PatchUserRequest): Partial update data

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    # Check if project exists if it's being updated
    project_canonical_name = data.project

    if project_canonical_name:
        project_exists_result = await project_exists(developer_id, project_canonical_name)

        if not project_exists_result[0]["project_exists"]:
            raise HTTPException(
                status_code=404, detail=f"Project '{project_canonical_name}' not found"
            )

    params = [
        developer_id,  # $1
        user_id,  # $2
        data.name,  # $3. Will be NULL if not provided
        data.about,  # $4. Will be NULL if not provided
        data.metadata,  # $5. Will be NULL if not provided
        project_canonical_name,  # $6. Will be NULL if not provided
    ]

    return (
        user_query,
        params,
    )
