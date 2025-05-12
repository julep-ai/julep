"""
This module contains the functionality for listing agents from the PostgreSQL database.
It constructs and executes SQL queries to fetch a list of agents based on developer ID with pagination.
"""

from typing import Any, Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Agent
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import (
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Define the raw SQL query
raw_query = """
SELECT
    a.agent_id,
    a.developer_id,
    a.name,
    a.canonical_name,
    a.about,
    a.instructions,
    a.model,
    a.metadata,
    a.default_settings,
    a.default_system_template,
    a.created_at,
    a.updated_at,
    p.canonical_name AS project
FROM
    agents a
LEFT JOIN project_agents pa ON a.agent_id = pa.agent_id AND a.developer_id = pa.developer_id
LEFT JOIN projects p ON pa.project_id = p.project_id AND pa.developer_id = p.developer_id
WHERE
    a.developer_id = $1 {metadata_filter_query}
ORDER BY
    CASE WHEN $4 = 'created_at' AND $5 = 'asc' THEN a.created_at END ASC NULLS LAST,
    CASE WHEN $4 = 'created_at' AND $5 = 'desc' THEN a.created_at END DESC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'asc' THEN a.updated_at END ASC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'desc' THEN a.updated_at END DESC NULLS LAST
LIMIT $2 OFFSET $3;
"""


@rewrap_exceptions(common_db_exceptions("agent", ["list"]))
@wrap_in_class(
    Agent,
    transform=lambda d: {**d, "id": d["agent_id"]},
)
@pg_query
@beartype
async def list_agents(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] | None = None,
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

    # AIDEV-NOTE: avoid mutable default; initialize metadata_filter
    metadata_filter = metadata_filter if metadata_filter is not None else {}
    # Initialize parameters
    params = [
        developer_id,
        limit,
        offset,
        sort_by,
        direction,
    ]

    # Handle metadata filter differently - using JSONB containment
    agent_query = raw_query.format(
        metadata_filter_query="AND a.metadata @> $6::jsonb" if metadata_filter else "",
    )

    # If we have metadata filters, safely add them as a parameter
    if metadata_filter:
        params.append(metadata_filter)

    return (
        agent_query,
        params,
    )
