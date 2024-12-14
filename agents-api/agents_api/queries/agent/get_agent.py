"""
This module contains the functionality for retrieving a single agent from the PostgreSQL database.
It constructs and executes SQL queries to fetch agent details based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException
from ...metrics.counters import increase_counter
from ..utils import (
    pg_query,
    partialclass,
    rewrap_exceptions,
    wrap_in_class,
)
from beartype import beartype
from psycopg import errors as psycopg_errors

from ...autogen.openapi_model import Agent

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

@rewrap_exceptions(
    {
        psycopg_errors.ForeignKeyViolation: partialclass(
            HTTPException, 
            status_code=404,
            detail="The specified developer does not exist."
        )
    }
    # TODO: Add more exceptions
)
@wrap_in_class(Agent, one=True)
@pg_query
@increase_counter("get_agent")
@beartype
def get_agent_query(*, agent_id: UUID, developer_id: UUID) -> tuple[list[str], dict]:
    """
    Constructs the SQL query to retrieve an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to retrieve.
        developer_id (UUID): The UUID of the developer owning the agent.

    Returns:
        tuple[list[str], dict]: A tuple containing the SQL query and its parameters.
    """
    query = """
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
        agent_id = %(agent_id)s AND developer_id = %(developer_id)s;
    """

    return (query, {"agent_id": agent_id, "developer_id": developer_id})
