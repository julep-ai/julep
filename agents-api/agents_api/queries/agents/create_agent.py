"""
This module contains the functionality for creating agents in the PostgreSQL database.
It includes functions to construct and execute SQL queries for inserting new agent records.
"""

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from uuid_extensions import uuid7

from ...autogen.openapi_model import Agent, CreateAgentRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..utils import generate_canonical_name, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating the agent
agent_query = """
WITH new_agent AS (
    INSERT INTO agents (
        developer_id,
        agent_id,
        canonical_name,
        name,
        about,
        instructions,
        model,
        metadata,
        default_settings,
        default_system_template
    )
    VALUES (
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        $7,
        $8,
        $9,
        $10
    )
    RETURNING *
), proj AS (
    -- Find project ID by canonical name
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $11
), project_association AS (
    -- Create project association if project exists
    INSERT INTO project_agents (project_id, developer_id, agent_id)
    SELECT p.project_id, $1, $2
    FROM proj p
    WHERE p.project_id IS NOT NULL
    ON CONFLICT (project_id, agent_id) DO NOTHING
    RETURNING 1
)
SELECT
    a.*,
    p.canonical_name AS project
FROM new_agent a
LEFT JOIN proj p ON TRUE;
"""


@rewrap_exceptions(common_db_exceptions("agent", ["create"]))
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"]},
)
@query_metrics("create_agent")
@pg_query
@beartype
async def create_agent(
    *,
    developer_id: UUID,
    agent_id: UUID | None = None,
    data: CreateAgentRequest,
) -> tuple[str, list]:
    """
    Constructs and executes a SQL query to create a new agent in the database.

    Parameters:
        agent_id (UUID | None): The unique identifier for the agent.
        developer_id (UUID): The unique identifier for the developer creating the agent.
        data (CreateAgentRequest): The data for the new agent.

    Returns:
        tuple[str, dict]: SQL query and parameters for creating the agent.
    """
    agent_id = agent_id or uuid7()
    project_canonical_name = data.project or "default"

    # First check if the project exists
    project_exists_result = await project_exists(developer_id, project_canonical_name)

    if not project_exists_result[0]["project_exists"]:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_canonical_name}' not found"
        )

    # Ensure instructions is a list
    data.instructions = (
        data.instructions if isinstance(data.instructions, list) else [data.instructions]
    )

    # Convert default_settings to dict if it exists
    default_settings = data.default_settings or {}

    # Set default values
    data.metadata = data.metadata or {}
    data.canonical_name = data.canonical_name or generate_canonical_name()

    params = [
        developer_id,
        agent_id,
        data.canonical_name,
        data.name,
        data.about,
        data.instructions,
        data.model,
        data.metadata,
        default_settings,
        data.default_system_template,
        project_canonical_name,
    ]

    return (
        agent_query,
        params,
    )
