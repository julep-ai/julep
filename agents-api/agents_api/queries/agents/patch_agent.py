"""
This module contains the functionality for partially updating an agent in the PostgreSQL database.
It constructs and executes SQL queries to update specific fields of an agent based on agent ID and developer ID.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import PatchAgentRequest, ResourceUpdatedResponse
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
    name = CASE 
        WHEN $3::text IS NOT NULL THEN $3 
        ELSE name 
    END,
    about = CASE 
        WHEN $4::text IS NOT NULL THEN $4 
        ELSE about 
    END,
    metadata = CASE 
        WHEN $5::jsonb IS NOT NULL THEN metadata || $5 
        ELSE metadata 
    END,
    model = CASE 
        WHEN $6::text IS NOT NULL THEN $6 
        ELSE model 
    END,
    default_settings = CASE 
        WHEN $7::jsonb IS NOT NULL THEN $7 
        ELSE default_settings 
    END
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
@increase_counter("patch_agent")
@pg_query
@beartype
async def patch_agent(
    *, agent_id: UUID, developer_id: UUID, data: PatchAgentRequest
) -> tuple[str, list]:
    """
    Constructs the SQL query to partially update an agent's details.

    Args:
        agent_id (UUID): The UUID of the agent to update.
        developer_id (UUID): The UUID of the developer owning the agent.
        data (PatchAgentRequest): A dictionary of fields to update.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.
    """
    params = [
        developer_id,
        agent_id,
        data.name,
        data.about,
        data.metadata,
        data.model,
        data.default_settings.model_dump() if data.default_settings else None,
    ]

    return query, params
