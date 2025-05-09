"""
This module contains the functionality for fully updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to replace an agent's details based on agent ID and developer ID.
"""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Agent, UpdateAgentRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
agent_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is provided and not NULL
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $9
    AND $9 IS NOT NULL
),
updated_agent AS (
    UPDATE agents
    SET
        metadata = $3,
        name = $4,
        about = $5,
        model = $6,
        default_settings = $7::jsonb,
        default_system_template = $8
    WHERE agent_id = $2 AND developer_id = $1
    RETURNING *
)
SELECT
    a.*,
    p.canonical_name as project
FROM updated_agent a
LEFT JOIN project_agents pa ON a.developer_id = pa.developer_id AND a.agent_id = pa.agent_id
LEFT JOIN projects p ON pa.project_id = p.project_id;
"""


@rewrap_exceptions(common_db_exceptions("agent", ["update"]))
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"]},
)
@query_metrics("update_agent")
@pg_query
@beartype
async def update_agent(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: UpdateAgentRequest,
) -> tuple[str, list]:
    """
    Constructs the SQL query to fully update an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to update.
        developer_id (UUID): The UUID of the developer owning the agent.
        data (UpdateAgentRequest): A dictionary containing all agent fields to update.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.
    """
    params = [
        developer_id,
        agent_id,
        data.metadata or {},
        data.name,
        data.about,
        data.model,
        data.default_settings or {},
        data.default_system_template,
        data.project,
    ]

    return (
        agent_query,
        params,
    )
