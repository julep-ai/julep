"""
This module contains the functionality for fully updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to replace an agent's details based on agent ID and developer ID.
"""

from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Agent, UpdateAgentRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
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
project_exists AS (
    -- Check if the project exists when specified
    SELECT
        CASE
            WHEN $9 IS NULL THEN TRUE -- No project specified, check passes
            WHEN EXISTS (SELECT 1 FROM proj) THEN TRUE -- Project exists
            ELSE FALSE -- Project specified but doesn't exist
        END AS exists
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
    AND (SELECT exists FROM project_exists)
    RETURNING *
)
SELECT
    (SELECT exists FROM project_exists) AS project_exists,
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
async def update_agent_query(
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


async def update_agent(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: UpdateAgentRequest,
    connection_pool: asyncpg.Pool | None = None,
) -> Agent:
    project_canonical_name = data.project or "default"
    project_exists_result = await project_exists(
        developer_id, project_canonical_name, connection_pool=connection_pool
    )

    if not project_exists_result[0]["project_exists"]:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_canonical_name}' not found"
        )

    return await update_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        data=data,
        connection_pool=connection_pool,
    )
