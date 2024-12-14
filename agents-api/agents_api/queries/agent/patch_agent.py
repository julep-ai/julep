"""
This module contains the functionality for partially updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to update specific fields of an agent based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from ...autogen.openapi_model import PatchAgentRequest, ResourceUpdatedResponse
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
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["agent_id"], **d},
    _kind="inserted",
)
@pg_query
@increase_counter("patch_agent")
@beartype
def patch_agent_query(
    *,
    agent_id: UUID,
    developer_id: UUID,
    data: PatchAgentRequest
) -> tuple[str, dict]:
    """
    Constructs the SQL query to partially update an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to update.
        developer_id (UUID): The UUID of the developer owning the agent.
        data (PatchAgentRequest): A dictionary of fields to update.

    Returns:
        tuple[str, dict]: A tuple containing the SQL query and its parameters.
    """
    patch_fields = data.model_dump(exclude_unset=True)
    set_clauses = []
    params = {}

    for key, value in patch_fields.items():
        if value is not None:  # Only update non-null values
            set_clauses.append(f"{key} = %({key})s")
            params[key] = value

    set_clause = ", ".join(set_clauses)
    
    query = f"""
    UPDATE agents
    SET {set_clause}
    WHERE agent_id = %(agent_id)s AND developer_id = %(developer_id)s
    RETURNING *;
    """

    params["agent_id"] = agent_id
    params["developer_id"] = developer_id

    return (query, params)
