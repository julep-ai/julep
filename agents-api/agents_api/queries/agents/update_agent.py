"""
This module contains the functionality for fully updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to replace an agent's details based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateAgentRequest
from ...metrics.counters import increase_counter
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

raw_query = """
UPDATE agents
SET 
    metadata = $3,
    name = $4,
    about = $5,
    model = $6,
    default_settings = $7::jsonb
WHERE agent_id = $2 AND developer_id = $1
RETURNING *;
"""

query = parse_one(raw_query).sql(pretty=True)


# @rewrap_exceptions(
#     {
#         psycopg_errors.ForeignKeyViolation: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="The specified developer does not exist.",
#         )
#     }
#     # TODO: Add more exceptions
# )
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["agent_id"], **d},
)
# @increase_counter("update_agent")
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
    print("*" * 100)
    print(query)
    print(params)
    print("*" * 100)
    return (query, params)
