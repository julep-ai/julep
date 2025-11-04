"""
This module contains the functionality for creating projects in the PostgreSQL database.
It includes functions to construct and execute SQL queries for inserting new project records.
"""

from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateProjectRequest, Project
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import generate_canonical_name, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
project_query = """
INSERT INTO projects (
    developer_id,
    project_id,
    canonical_name,
    name,
    description,
    metadata
)
VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6
)
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("project", ["create"]))
@wrap_in_class(
    Project,
    one=True,
    transform=lambda d: {**d, "id": d["project_id"]},
)
@query_metrics("create_project")
@pg_query
@beartype
async def create_project(
    *,
    developer_id: UUID,
    project_id: UUID | None = None,
    data: CreateProjectRequest,
) -> tuple[str, list]:
    """
    Constructs and executes a SQL query to create a new project in the database.

    Parameters:
        project_id (UUID | None): The unique identifier for the project.
        developer_id (UUID): The unique identifier for the developer creating the project.
        data (CreateProjectRequest): The data for the new project.

    Returns:
        tuple[str, dict]: SQL query and parameters for creating the project.
    """
    project_id = project_id or uuid7()

    # Set default values
    data.metadata = data.metadata or {}
    data.canonical_name = data.canonical_name or generate_canonical_name()

    params = [
        developer_id,
        project_id,
        data.canonical_name,
        data.name,
        data.description,
        data.metadata,
    ]

    return (
        project_query,
        params,
    )
