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
    build_metadata_filter_conditions,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Define the base SQL query without dynamic parts
base_query = """
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
    a.developer_id = $1
"""

# ORDER BY clause template
order_by_clause = """
ORDER BY
    CASE WHEN $2 = 'created_at' AND $3 = 'asc' THEN a.created_at END ASC NULLS LAST,
    CASE WHEN $2 = 'created_at' AND $3 = 'desc' THEN a.created_at END DESC NULLS LAST,
    CASE WHEN $2 = 'updated_at' AND $3 = 'asc' THEN a.updated_at END ASC NULLS LAST,
    CASE WHEN $2 = 'updated_at' AND $3 = 'desc' THEN a.updated_at END DESC NULLS LAST
LIMIT $4 OFFSET $5;
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

    # Initialize base parameters
    params = [
        developer_id,
        sort_by,
        direction,
        limit,
        offset,
    ]

    # Start building the query
    query = base_query

    # Add metadata filter conditions if provided
    if metadata_filter:
        # Use the existing utility function to build metadata filter conditions
        filter_conditions, filter_params = build_metadata_filter_conditions(
            base_params=params,
            metadata_filter=metadata_filter,
            table_alias="a.",
        )
        query += filter_conditions
        params = filter_params

    # Add ORDER BY and LIMIT clauses
    query += order_by_clause

    return (query, params)
