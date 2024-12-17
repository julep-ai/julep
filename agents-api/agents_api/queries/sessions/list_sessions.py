"""This module contains functions for querying session data from the PostgreSQL database."""

from typing import Any, Literal, TypeVar
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Session
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
raw_query = """
WITH session_participants AS (
    SELECT 
        sl.session_id,
        array_agg(sl.participant_id) FILTER (WHERE sl.participant_type = 'agent') as agents,
        array_agg(sl.participant_id) FILTER (WHERE sl.participant_type = 'user') as users
    FROM session_lookup sl
    WHERE sl.developer_id = $1
    GROUP BY sl.session_id
)
SELECT 
    s.session_id as id,
    s.developer_id,
    s.situation,
    s.system_template,
    s.metadata,
    s.render_templates,
    s.token_budget,
    s.context_overflow,
    s.forward_tool_calls,
    s.recall_options,
    s.created_at,
    s.updated_at,
    sp.agents,
    sp.users
FROM sessions s
LEFT JOIN session_participants sp ON s.session_id = sp.session_id
WHERE s.developer_id = $1
    AND ($5::jsonb IS NULL OR s.metadata @> $5::jsonb)
ORDER BY 
    CASE WHEN $3 = 'created_at' AND $4 = 'desc' THEN s.created_at END DESC,
    CASE WHEN $3 = 'created_at' AND $4 = 'asc' THEN s.created_at END ASC,
    CASE WHEN $3 = 'updated_at' AND $4 = 'desc' THEN s.updated_at END DESC,
    CASE WHEN $3 = 'updated_at' AND $4 = 'asc' THEN s.updated_at END ASC
LIMIT $2 OFFSET $6;
"""

# Parse and optimize the query
# query = parse_one(raw_query).sql(pretty=True)
query = raw_query


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.NoDataFoundError: partialclass(
            HTTPException, status_code=404, detail="No sessions found"
        ),
    }
)
@wrap_in_class(Session)
@increase_counter("list_sessions")
@pg_query
@beartype
async def list_sessions(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, list]:
    """
    Lists sessions from the PostgreSQL database based on the provided filters.

    Args:
        developer_id (UUID): The developer's UUID
        limit (int): Maximum number of sessions to return
        offset (int): Number of sessions to skip
        sort_by (str): Field to sort by ('created_at' or 'updated_at')
        direction (str): Sort direction ('asc' or 'desc')
        metadata_filter (dict): Dictionary of metadata fields to filter by

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    return (
        query,
        [
            developer_id,  # $1
            limit,  # $2
            sort_by,  # $3
            direction,  # $4
            metadata_filter or None,  # $5
            offset,  # $6
        ],
    )
