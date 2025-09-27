"""
This module contains the functionality for retrieving a single agent from the PostgreSQL database.
It constructs and executes SQL queries to fetch agent details based on agent ID and developer ID.
"""

from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Agent
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
agent_query = """
SELECT
    a.agent_id,
    a.developer_id,
    a.name,
    a.canonical_name,
    a.about,
    a.instructions,
    a.model,
    a.metadata,
    a.default_settings,
    a.default_system_template,
    a.created_at,
    a.updated_at,
    p.canonical_name AS project
FROM
    agents a
LEFT JOIN project_agents pa ON a.agent_id = pa.agent_id AND a.developer_id = pa.developer_id
LEFT JOIN projects p ON pa.project_id = p.project_id AND pa.developer_id = p.developer_id
WHERE
    a.agent_id = $2 AND a.developer_id = $1;
"""


@rewrap_exceptions(common_db_exceptions("agent", ["get"]))
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"]},
)
@pg_query
@beartype
async def get_agent(
    *,
    agent_id: UUID,
    developer_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Constructs the SQL query to retrieve an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to retrieve.
        developer_id (UUID): The UUID of the developer owning the agent.

    Returns:
        tuple[list[str], dict]: A tuple containing the SQL query and its parameters.
    """

    return (
        agent_query,
        [developer_id, agent_id],
        "fetchrow",
    )
