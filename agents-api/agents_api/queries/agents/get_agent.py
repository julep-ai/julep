"""
This module contains the functionality for retrieving a single agent from the PostgreSQL database.
It constructs and executes SQL queries to fetch agent details based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import Agent
from ...metrics.counters import increase_counter
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

raw_query = """
SELECT 
    agent_id,
    developer_id,
    name,
    canonical_name,
    about,
    instructions,
    model,
    metadata,
    default_settings,
    created_at,
    updated_at
FROM 
    agents
WHERE 
    agent_id = $2 AND developer_id = $1;
"""

query = parse_one(raw_query).sql(pretty=True)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


# @rewrap_exceptions(
# {
#     psycopg_errors.ForeignKeyViolation: partialclass(
#         HTTPException,
#         status_code=404,
#         detail="The specified developer does not exist.",
#     )
# }
# # TODO: Add more exceptions
# )
@wrap_in_class(Agent, one=True, transform=lambda d: {"id": d["agent_id"], **d})
@increase_counter("get_agent")
@pg_query
@beartype
async def get_agent(*, agent_id: UUID, developer_id: UUID) -> tuple[str, list]:
    """
    Constructs the SQL query to retrieve an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to retrieve.
        developer_id (UUID): The UUID of the developer owning the agent.

    Returns:
        tuple[list[str], dict]: A tuple containing the SQL query and its parameters.
    """

    return (query, [developer_id, agent_id])
