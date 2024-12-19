from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import History
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for getting history with a developer check
history_query = parse_one("""
SELECT 
    e.entry_id as id, -- entry_id
    e.session_id, -- session_id
    e.role, -- role
    e.name, -- name
    e.content, -- content
    e.source, -- source
    e.token_count, -- token_count
    e.created_at, -- created_at
    e.timestamp, -- timestamp
    e.tool_calls, -- tool_calls
    e.tool_call_id -- tool_call_id
FROM entries e
JOIN developers d ON d.developer_id = $3
WHERE e.session_id = $1
AND e.source = ANY($2)
ORDER BY e.created_at;
""").sql(pretty=True)


# @rewrap_exceptions(
#     {
#         asyncpg.ForeignKeyViolationError: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="Session not found",
#         ),
#         asyncpg.UniqueViolationError: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="Session not found",
#         ),
#     }
# )
@wrap_in_class(
    History,
    one=True,
    transform=lambda d: {
        **d,
        "relations": [
            {
                "head": r["head"],
                "relation": r["relation"],
                "tail": r["tail"],
            }
            for r in d.pop("relations")
        ],
        "entries": d.pop("entries"),
    },
)
@pg_query
@beartype
async def get_history(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
) -> tuple[str, list]:
    return (
        history_query,
        [session_id, allowed_sources, developer_id],
    )
