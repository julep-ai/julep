"""
This module contains the functionality for creating agents in the PostgreSQL database.
It includes functions to construct and execute SQL queries for inserting new agent records.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pydantic import ValidationError
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import Agent, CreateAgentRequest
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
#         ),
#         psycopg_errors.UniqueViolation: partialclass(
#             HTTPException,
#             status_code=409,
#             detail="An agent with this canonical name already exists for this developer.",
#         ),
#         psycopg_errors.CheckViolation: partialclass(
#             HTTPException,
#             status_code=400,
#             detail="The provided data violates one or more constraints. Please check the input values.",
#         ),
#         ValidationError: partialclass(
#             HTTPException,
#             status_code=400,
#             detail="Input validation failed. Please check the provided data.",
#         ),
#         TypeError: partialclass(
#             HTTPException,
#             status_code=400,
#             detail="A type mismatch occurred. Please review the input.",
#         ),
#     }
# )
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {"id": d["agent_id"], **d},
)
# @increase_counter("create_agent")
@pg_query
@beartype
async def create_agent(
    *,
    developer_id: UUID,
    agent_id: UUID | None = None,
    data: CreateAgentRequest,
) -> tuple[str, list]:
    """
    Constructs and executes a SQL query to create a new agent in the database.

    Parameters:
        agent_id (UUID | None): The unique identifier for the agent.
        developer_id (UUID): The unique identifier for the developer creating the agent.
        data (CreateAgentRequest): The data for the new agent.

    Returns:
        tuple[str, dict]: SQL query and parameters for creating the agent.
    """
    agent_id = agent_id or uuid7()

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

    return query, params
