"""
This module contains the functionality for fully updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to replace an agent's details based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

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
    transform=lambda d: {"id": d["agent_id"], "jobs": [], **d},
    _kind="inserted",
)
@pg_query
# @increase_counter("update_agent1")
@beartype
async def update_agent(
    *, agent_id: UUID, developer_id: UUID, data: UpdateAgentRequest
) -> tuple[str, dict]:
    """
    Constructs the SQL query to fully update an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to update.
        developer_id (UUID): The UUID of the developer owning the agent.
        data (UpdateAgentRequest): A dictionary containing all agent fields to update.

    Returns:
        tuple[str, dict]: A tuple containing the SQL query and its parameters.
    """
    fields = ", ".join(
        [f"{key} = %({key})s" for key in data.model_dump(exclude_unset=True).keys()]
    )
    params = {key: value for key, value in data.model_dump(exclude_unset=True).items()}

    query = f"""
    UPDATE agents
    SET {fields}
    WHERE agent_id = %(agent_id)s AND developer_id = %(developer_id)s
    RETURNING *;
    """

    params["agent_id"] = agent_id
    params["developer_id"] = developer_id

    return (query, params)
