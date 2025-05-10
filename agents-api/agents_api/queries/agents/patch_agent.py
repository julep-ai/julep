"""
This module contains the functionality for partially updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to update specific fields of an agent based on agent ID and developer ID.
"""

from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Agent, PatchAgentRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..projects.project_exists import project_exists
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
agent_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is being updated
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $11
    AND $11 IS NOT NULL
),
project_exists AS (
    -- Check if project exists when being updated
    SELECT
        CASE
            WHEN $11 IS NULL THEN TRUE -- No project specified, so exists check passes
            WHEN EXISTS (SELECT 1 FROM proj) THEN TRUE -- Project exists
            ELSE FALSE -- Project specified but doesn't exist
        END AS exists
),
updated_agent AS (
    UPDATE agents
    SET
        name = CASE
            WHEN $3::text IS NOT NULL THEN $3
            ELSE name
        END,
        about = CASE
            WHEN $4::text IS NOT NULL THEN $4
            ELSE about
        END,
        metadata = CASE
            WHEN $5::jsonb IS NOT NULL THEN metadata || $5
            ELSE metadata
        END,
        model = CASE
            WHEN $6::text IS NOT NULL THEN $6
            ELSE model
        END,
        default_settings = CASE
            WHEN $7::jsonb IS NOT NULL THEN $7
            ELSE default_settings
        END,
        default_system_template = CASE
            WHEN $8::text IS NOT NULL THEN $8
            ELSE default_system_template
        END,
        instructions = CASE
            WHEN $9::text[] IS NOT NULL THEN $9
            ELSE instructions
        END,
        canonical_name = CASE
            WHEN $10::citext IS NOT NULL THEN $10
            ELSE canonical_name
        END
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


@rewrap_exceptions(common_db_exceptions("agent", ["patch"]))
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"]},
)
@query_metrics("patch_agent")
@pg_query
@beartype
async def patch_agent_query(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: PatchAgentRequest,
) -> tuple[str, list]:
    """
    Constructs the SQL query to partially update an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to update.
        developer_id (UUID): The UUID of the developer owning the agent.
        data (PatchAgentRequest): A dictionary of fields to update.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.
    """
    params = [
        developer_id,
        agent_id,
        data.name,
        data.about,
        data.metadata,
        data.model,
        data.default_settings,
        data.default_system_template,
        [data.instructions] if isinstance(data.instructions, str) else data.instructions,
        data.canonical_name,
        data.project,
    ]

    return (
        agent_query,
        params,
    )


async def patch_agent(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: PatchAgentRequest,
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

    return await patch_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        data=data,
        connection_pool=connection_pool,
    )
