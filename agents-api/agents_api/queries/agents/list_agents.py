"""
This module contains the functionality for listing agents from the PostgreSQL database.
It constructs and executes SQL queries to fetch a list of agents based on developer ID with pagination.
"""

from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Agent
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
@wrap_in_class(Agent)
@pg_query
# @increase_counter("list_agents1")
@beartype
async def list_agents(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, dict]:
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
    metadata_clause = ""
    if metadata_filter:
        metadata_clause = "AND metadata @> %(metadata_filter)s::jsonb"

    query = f"""
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
    WHERE developer_id = %(developer_id)s
    {metadata_clause}
    ORDER BY {sort_by} {direction}
    LIMIT %(limit)s OFFSET %(offset)s;
    """

    params = {"developer_id": developer_id, "limit": limit, "offset": offset}

    if metadata_filter:
        params["metadata_filter"] = metadata_filter

    return query, params
