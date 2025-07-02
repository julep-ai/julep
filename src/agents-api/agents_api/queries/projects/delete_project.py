"""
This module contains the functionality for deleting projects from the PostgreSQL database.
It constructs and executes SQL queries to remove project records and associated data.
"""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Delete project query that handles RESTRICT constraints by deleting associations first
delete_project_query = """
-- First check if the project exists and is not the default project
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM projects 
        WHERE developer_id = $1 AND project_id = $2
    ) THEN
        RAISE EXCEPTION 'Project not found';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM projects 
        WHERE developer_id = $1 AND project_id = $2 AND canonical_name = 'default'
    ) THEN
        RAISE EXCEPTION 'Cannot delete default project';
    END IF;
END $$;

-- Delete all project associations to handle RESTRICT constraints
DELETE FROM project_agents WHERE project_id = $2 AND developer_id = $1;
DELETE FROM project_users WHERE project_id = $2 AND developer_id = $1;
DELETE FROM project_files WHERE project_id = $2 AND developer_id = $1;

-- Then delete the project itself
DELETE FROM projects
WHERE developer_id = $1
AND project_id = $2
RETURNING project_id;
"""


@rewrap_exceptions(common_db_exceptions("project", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["project_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@query_metrics("delete_project")
@pg_query
@beartype
async def delete_project(
    *,
    developer_id: UUID,
    project_id: UUID,
) -> tuple[str, list]:
    """
    Deletes a project and all its associations.

    Args:
        developer_id: The developer's UUID
        project_id: The project's UUID

    Returns:
        tuple[str, list]: SQL query and parameters
        
    Raises:
        Exception: If project not found or is the default project
    """
    return (
        delete_project_query,
        [developer_id, project_id],
    ) 