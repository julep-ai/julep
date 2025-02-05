"""
This module contains the functionality for partially updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to update specific fields of an agent based on agent ID and developer ID.
"""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Agent, PatchAgentRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
agent_query = """
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
    instructions = CASE
		WHEN $8::text[] IS NOT NULL THEN $8
		ELSE instructions
	END,
    canonical_name = CASE
        WHEN $9::citext IS NOT NULL THEN $9
        ELSE canonical_name
    END
WHERE agent_id = $2 AND developer_id = $1
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("agent", ["patch"]))
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"]},
)
@increase_counter("patch_agent")
@pg_query
@beartype
async def patch_agent(
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
        [data.instructions] if isinstance(data.instructions, str) else data.instructions,
        data.canonical_name,
    ]

    return (
        agent_query,
        params,
    )
