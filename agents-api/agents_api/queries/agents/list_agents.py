"""
This module contains the functionality for listing agents from the PostgreSQL database.
It constructs and executes SQL queries to fetch a list of agents based on developer ID with pagination.
"""

from typing import Any, Literal, TypeVar
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

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

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
FROM agents
WHERE developer_id = $1 {metadata_filter_query}
ORDER BY 
    CASE WHEN $4 = 'created_at' AND $5 = 'asc' THEN created_at END ASC NULLS LAST,
    CASE WHEN $4 = 'created_at' AND $5 = 'desc' THEN created_at END DESC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'asc' THEN updated_at END ASC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'desc' THEN updated_at END DESC NULLS LAST
LIMIT $2 OFFSET $3;
"""


#  @rewrap_exceptions(
#     {
#         psycopg_errors.ForeignKeyViolation: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="The specified developer does not exist.",
#         )
#     }
#     # TODO: Add more exceptions
# )
@wrap_in_class(Agent, transform=lambda d: {"id": d["agent_id"], **d})
@increase_counter("list_agents")
@pg_query
@beartype
async def list_agents(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, list]:
    """
    Constructs query to list agents for a developer with pagination.

    Args:
        developer_id: UUID of the developer
        limit: Maximum number of records to return
        offset: Number of records to skip
        sort_by: Field to sort by
        direction: Sort direction ('asc' or 'desc')
        metadata_filter: Optional metadata filters

    Returns:
        Tuple of (query, params)
    """
    # Validate sort direction
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    # Build metadata filter clause if needed

    final_query = raw_query.format(
        metadata_filter_query="AND metadata @> $6::jsonb" if metadata_filter else ""
    )

    params = [
        developer_id,
        limit,
        offset,
        sort_by,
        direction,
    ]

    if metadata_filter:
        params.append(metadata_filter)

    return final_query, params
