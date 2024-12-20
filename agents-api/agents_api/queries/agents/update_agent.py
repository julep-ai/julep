"""
This module contains the functionality for fully updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to replace an agent's details based on agent ID and developer ID.
"""

from uuid import UUID

from beartype import beartype
from sqlglot import parse_one
from fastapi import HTTPException
import asyncpg
from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateAgentRequest
from ...metrics.counters import increase_counter
from ..utils import (
    pg_query,
    wrap_in_class,
    rewrap_exceptions,
    partialclass,
)

# Define the raw SQL query
agent_query = parse_one("""
UPDATE agents
SET 
    metadata = $3,
    name = $4,
    about = $5,
    model = $6,
    default_settings = $7::jsonb
WHERE agent_id = $2 AND developer_id = $1
RETURNING *;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.exceptions.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.exceptions.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="An agent with this canonical name already exists for this developer.",
        ),
        asyncpg.exceptions.CheckViolationError: partialclass(
            HTTPException,
            status_code=400,
            detail="The provided data violates one or more constraints. Please check the input values.",
        ),
        asyncpg.exceptions.DataError: partialclass(
            HTTPException,
            status_code=400,
            detail="Invalid data provided. Please check the input values.",
        ),
    }
)
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["agent_id"], **d},
)
@increase_counter("update_agent")
@pg_query
@beartype
async def update_agent(
    *, agent_id: UUID, developer_id: UUID, data: UpdateAgentRequest
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
        data.default_settings.model_dump() if data.default_settings else {},
    ]

    return (
        agent_query,
        params,
    )
