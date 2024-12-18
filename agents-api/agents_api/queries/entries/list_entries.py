from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Entry
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query for checking if the session exists
session_exists_query = """
SELECT CASE
    WHEN EXISTS (
        SELECT 1 FROM sessions
        WHERE session_id = $1 AND developer_id = $2
    )
    THEN TRUE
    ELSE (SELECT NULL::boolean WHERE FALSE)  -- This raises a NO_DATA_FOUND error
END;
"""

list_entries_query = """
SELECT 
    e.entry_id as id,
    e.session_id,
    e.role,
    e.name,
    e.content,
    e.source,
    e.token_count,
    e.created_at,
    e.timestamp,
    e.event_type,
    e.tool_call_id,
    e.tool_calls,
    e.model
FROM entries e
JOIN developers d ON d.developer_id = $5
LEFT JOIN entry_relations er ON er.head = e.entry_id AND er.session_id = e.session_id
WHERE e.session_id = $1
AND e.source = ANY($2)
AND (er.relation IS NULL OR er.relation != ALL($6))
ORDER BY e.{sort_by} {direction} -- safe to interpolate
LIMIT $3 
OFFSET $4;
"""


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: lambda exc: HTTPException(
            status_code=404,
            detail=str(exc),
        ),
        asyncpg.UniqueViolationError: lambda exc: HTTPException(
            status_code=409,
            detail=str(exc),
        ),
        asyncpg.NotNullViolationError: lambda exc: HTTPException(
            status_code=400,
            detail=str(exc),
        ),
    }
)
@wrap_in_class(Entry)
@increase_counter("list_entries")
@pg_query
@beartype
async def list_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "timestamp"] = "timestamp",
    direction: Literal["asc", "desc"] = "asc",
    exclude_relations: list[str] = [],
) -> list[tuple[str, list]]:
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    query = list_entries_query.format(
        sort_by=sort_by,
        direction=direction,
    )

    # Parameters for the entry query
    entry_params = [
        session_id,  # $1
        allowed_sources,  # $2
        limit,  # $3
        offset,  # $4
        developer_id,  # $5
        exclude_relations,  # $6
    ]

    return [
        (
            session_exists_query,
            [session_id, developer_id],
        ),
        (
            query,
            entry_params,
        ),
    ]

