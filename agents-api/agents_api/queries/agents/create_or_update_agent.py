"""
This module contains the functionality for creating or updating agents in the PostgreSQL database.
It constructs and executes SQL queries to insert a new agent or update an existing agent's details based on agent ID and developer ID.
"""

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Agent, CreateOrUpdateAgentRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..utils import generate_canonical_name, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
agent_query = """
WITH existing_agent AS (
    SELECT canonical_name
    FROM agents
    WHERE developer_id = $1 AND agent_id = $2
), proj AS (
    -- Find project ID by canonical name
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $11
)
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
    default_system_template,
    project_id
)
VALUES (
    $1,                                          -- developer_id
    $2,                                          -- agent_id
    COALESCE(                                    -- canonical_name
        (SELECT canonical_name FROM existing_agent),
        $3
    ),
    $4,                                          -- name
    $5,                                          -- about
    $6,                                          -- instructions
    $7,                                          -- model
    $8,                                          -- metadata
    $9,                                          -- default_settings
    $10,                                         -- default_system_template
    (SELECT project_id FROM proj)                -- project_id
)
ON CONFLICT (developer_id, agent_id) DO UPDATE SET
    canonical_name = EXCLUDED.canonical_name,
    name = EXCLUDED.name,
    about = EXCLUDED.about,
    instructions = EXCLUDED.instructions,
    model = EXCLUDED.model,
    metadata = EXCLUDED.metadata,
    default_settings = EXCLUDED.default_settings,
    default_system_template = EXCLUDED.default_system_template,
    project_id = (SELECT project_id FROM proj)
RETURNING 
    agents.*,
    (SELECT canonical_name FROM proj) AS project;
"""


@rewrap_exceptions(common_db_exceptions("agent", ["create", "update"]))
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"]},
)
@query_metrics("create_or_update_agent")
@pg_query
@beartype
async def create_or_update_agent(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: CreateOrUpdateAgentRequest,
) -> tuple[str, list]:
    """
    Constructs the SQL queries to create a new agent or update an existing agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to create or update.
        developer_id (UUID): The UUID of the developer owning the agent.
        data (CreateOrUpdateAgentRequest): A dictionary containing agent fields to insert or update.

    Returns:
        tuple[list[str], dict]: A tuple containing the list of SQL queries and their parameters.
    """
    # Get project (default if not specified)
    project_canonical_name = (
        data.project if hasattr(data, "project") and data.project else "default"
    )
    
    # Check if the project exists
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
