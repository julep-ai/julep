"""
This module contains the functionality for creating or updating agents in the PostgreSQL database.
It constructs and executes SQL queries to insert a new agent or update an existing agent's details based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from psycopg import errors as psycopg_errors

from ...autogen.openapi_model import Agent, CreateOrUpdateAgentRequest
from ..utils import (
    # generate_canonical_name,
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        psycopg_errors.ForeignKeyViolation: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        )
    }
)
@wrap_in_class(
    Agent,
    one=True,
    transform=lambda d: {"id": d["agent_id"], **d},
    _kind="inserted",
)
@pg_query
# @increase_counter("create_or_update_agent1")
@beartype
def create_or_update_agent_query(
    *, agent_id: UUID, developer_id: UUID, data: CreateOrUpdateAgentRequest
) -> tuple[list[str], dict]:
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
        data.default_settings.model_dump() if data.default_settings else None
    )

    # Set default values
    data.metadata = data.metadata or None
    # data.canonical_name = data.canonical_name or generate_canonical_name(data.name)

    query = """
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
        %(developer_id)s,
        %(agent_id)s,
        %(canonical_name)s,
        %(name)s,
        %(about)s,
        %(instructions)s,
        %(model)s,
        %(metadata)s,
        %(default_settings)s
    )
    RETURNING *;
    """

    params = {
        "developer_id": developer_id,
        "agent_id": agent_id,
        "canonical_name": data.canonical_name,
        "name": data.name,
        "about": data.about,
        "instructions": data.instructions,
        "model": data.model,
        "metadata": data.metadata,
        "default_settings": default_settings,
    }

    return (query, params)
