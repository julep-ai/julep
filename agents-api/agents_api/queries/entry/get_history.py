from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import History
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for getting history
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
    e.timestamp,
    e.tool_calls,
    e.tool_call_id
FROM entries e
WHERE e.session_id = $1
AND e.source = ANY($2)
ORDER BY e.created_at;
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
            "tool_calls": "JSONB",
            "tool_call_id": "UUID",
        }
    },
).sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(History, one=True)
@increase_counter("get_history")
@pg_query
@beartype
def get_history(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
) -> tuple[str, dict]:
    return (
        query,
        [session_id, allowed_sources],
    )
