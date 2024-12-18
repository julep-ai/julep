"""
This module contains the functionality for creating or updating agents in the PostgreSQL database.
It constructs and executes SQL queries to insert a new agent or update an existing agent's details based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import Agent, CreateOrUpdateAgentRequest
from ...metrics.counters import increase_counter
from ..utils import (
    generate_canonical_name,
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

raw_query = """
INSERT INTO agents (
    developer_id,
    agent_id,
    canonical_name,
    name,
    about,
    instructions,
    model,
    metadata,
    default_settings
)
VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
    $9
)
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
# )
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {"id": d["agent_id"], **d},
)
@increase_counter("create_or_update_agent")
@pg_query
@beartype
async def create_or_update_agent(
    *, agent_id: UUID, developer_id: UUID, data: CreateOrUpdateAgentRequest
) -> tuple[str, list]:
    """
    Constructs the SQL queries to create a new agent or update an existing agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to create or update.
        developer_id (UUID): The UUID of the developer owning the agent.
        agent_data (Dict[str, Any]): A dictionary containing agent fields to insert or update.

    Returns:
        tuple[list[str], dict]: A tuple containing the list of SQL queries and their parameters.
    """

    # Ensure instructions is a list
    data.instructions = (
        data.instructions
        if isinstance(data.instructions, list)
        else [data.instructions]
    )

    # Convert default_settings to dict if it exists
    default_settings = (
        data.default_settings.model_dump() if data.default_settings else {}
    )

    # Set default values
    data.metadata = data.metadata or {}
    data.canonical_name = data.canonical_name or generate_canonical_name(data.name)

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
    ]

    return (query, params)
