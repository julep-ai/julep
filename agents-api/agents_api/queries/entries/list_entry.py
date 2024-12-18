from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Entry
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

entry_query = """
SELECT 
    e.entry_id as id, -- entry_id
    e.session_id, -- session_id
    e.role, -- role
    e.name, -- name
    e.content, -- content
    e.source, -- source
    e.token_count, -- token_count
    e.created_at, -- created_at
    e.timestamp -- timestamp
FROM entries e
JOIN developers d ON d.developer_id = $7
LEFT JOIN entry_relations er ON er.head = e.entry_id AND er.session_id = e.session_id
WHERE e.session_id = $1
AND e.source = ANY($2)
AND (er.relation IS NULL OR er.relation != ALL($8))
ORDER BY e.$3 $4
LIMIT $5 
OFFSET $6;
"""


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: lambda exc: HTTPException(
            status_code=404,
            detail=str(exc),
        ),
        asyncpg.UniqueViolationError: lambda exc: HTTPException(
            status_code=404,
            detail=str(exc),
        ),
    }
)
@wrap_in_class(Entry)
@pg_query
@beartype
async def list_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
    limit: int = 1,
    offset: int = 0,
    sort_by: Literal["created_at", "timestamp"] = "timestamp",
    direction: Literal["asc", "desc"] = "asc",
    exclude_relations: list[str] = [],
) -> tuple[str, list]:
    
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")
    
    # making the parameters for the query
    params = [
        session_id,  # $1
        allowed_sources,  # $2
        sort_by,  # $3
        direction,  # $4
        limit,  # $5
        offset,  # $6
        developer_id,  # $7
        exclude_relations,  # $8
    ]
    return (
        entry_query,
        params,
    )
