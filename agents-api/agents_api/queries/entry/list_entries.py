from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import Entry
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for listing entries
raw_query = """
SELECT 
    e.entry_id as id,
    e.session_id,
    e.role,
    e.name,
    e.content,
    e.source,
    e.token_count,
    e.created_at,
    e.timestamp
FROM entries e
WHERE e.session_id = $1
AND e.source = ANY($2)
ORDER BY e.$3 $4
LIMIT $5 OFFSET $6;
"""

# Parse and optimize the query
query = optimize(
    parse_one(raw_query),
    schema={
        "entries": {
            "entry_id": "UUID",
            "session_id": "UUID",
            "role": "STRING",
            "name": "STRING",
            "content": "JSONB",
            "source": "STRING",
            "token_count": "INTEGER",
            "created_at": "TIMESTAMP",
            "timestamp": "TIMESTAMP",
        }
    },
).sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(Entry)
@increase_counter("list_entries")
@pg_query
@beartype
def list_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
    limit: int = -1,
    offset: int = 0,
    sort_by: Literal["created_at", "timestamp"] = "timestamp",
    direction: Literal["asc", "desc"] = "asc",
    exclude_relations: list[str] = [],
) -> tuple[str, dict]:
    return (
        query,
        [session_id, allowed_sources, sort_by, direction, limit, offset],
    )
