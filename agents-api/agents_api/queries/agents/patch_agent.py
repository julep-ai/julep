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
from ..sql_builder import build_patch_query
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Base query to check project and get agent after update
agent_select_query = """
WITH proj AS (
    -- Find project ID by canonical name if project is being updated
    SELECT project_id, canonical_name
    FROM projects
    WHERE developer_id = $1 AND canonical_name = $2
    AND $2 IS NOT NULL
),
project_exists AS (
    -- Check if project exists when being updated
    SELECT
        CASE
            WHEN $2 IS NULL THEN TRUE -- No project specified, so exists check passes
            WHEN EXISTS (SELECT 1 FROM proj) THEN TRUE -- Project exists
            ELSE FALSE -- Project specified but doesn't exist
        END AS exists
),
updated_agent AS (
    -- UPDATE_PLACEHOLDER
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
) -> tuple[str, list] | list[tuple[str, list]]:
    """
    Constructs the SQL query to partially update an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to update.
        developer_id (UUID): The UUID of the developer owning the agent.
        data (PatchAgentRequest): A dictionary of fields to update.

    Returns:
        tuple[str, list] | list[tuple[str, list]]: SQL query(ies) and parameters.
    """
    # Prepare patch data, handling special cases
    patch_fields = {
        "name": data.name,
        "about": data.about,
        "model": data.model,
        "default_settings": data.default_settings,
        "default_system_template": data.default_system_template,
        "canonical_name": data.canonical_name,
    }

    # Handle metadata (merge operation)
    if data.metadata is not None:
        patch_fields["metadata"] = data.metadata

    # Handle instructions (convert string to array if needed)
    if data.instructions is not None:
        patch_fields["instructions"] = (
            [data.instructions]
            if isinstance(data.instructions, str)
            else data.instructions
        )

    # Filter out None values
    update_fields = {k: v for k, v in patch_fields.items() if v is not None}

    # If no fields to update, just return the agent
    if not update_fields:
        simple_select = """
        SELECT
            a.*,
            p.canonical_name as project
        FROM agents a
        LEFT JOIN project_agents pa ON a.developer_id = pa.developer_id AND a.agent_id = pa.agent_id
        LEFT JOIN projects p ON pa.project_id = p.project_id
        WHERE a.agent_id = $1 AND a.developer_id = $2;
        """
        return (simple_select, [agent_id, developer_id])

    # Build the UPDATE query - cast UUIDs to proper types
    # Note: We already have 2 parameters in the outer query ($1 and $2), so start from 3
    update_query, update_params = build_patch_query(
        table_name="agents",
        patch_data=update_fields,
        where_conditions={"agent_id": str(agent_id), "developer_id": str(developer_id)},
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
    final_query = agent_select_query.replace("-- UPDATE_PLACEHOLDER", update_query)

    # Combine parameters: developer_id, project_name, then update params
    all_params = [str(developer_id), data.project, *update_params]

    return (final_query, all_params)


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
