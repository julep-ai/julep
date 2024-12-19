from uuid import UUID
import json
from typing import Tuple, List, Any

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import History
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

from ...common.utils.datetime import utcnow

# Define the raw SQL query for getting history with a developer check and relations
history_query = parse_one("""
WITH entries AS (
    SELECT 
        e.entry_id AS id,
        e.session_id,
        e.role,
        e.name,
        e.content,
        e.source,
        e.token_count,
        e.created_at,
        e.timestamp,
        e.tool_calls,
        e.tool_call_id,
        e.tokenizer
    FROM entries e
    JOIN developers d ON d.developer_id = $3
    WHERE e.session_id = $1
    AND e.source = ANY($2)
),
relations AS (
    SELECT 
        er.head,
        er.relation,
        er.tail
    FROM entry_relations er
    WHERE er.session_id = $1
)
SELECT 
    (SELECT json_agg(e) FROM entries e) AS entries,
    (SELECT json_agg(r) FROM relations r) AS relations,
    $1::uuid AS session_id,
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="Session not found",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="Entry already exists",
        ),
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="Session not found",
        ),
    }
)
@wrap_in_class(
    History,
    one=True,
    transform=lambda d: {
        "entries": json.loads(d.get("entries") or "[]"),
        "relations": [
            {
                "head": r["head"],
                "relation": r["relation"],
                "tail": r["tail"],
            }
            for r in (d.get("relations") or [])
        ],
        "session_id": d.get("session_id"),
        "created_at": utcnow(),
    },
)
@pg_query
@beartype
async def get_history(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
) -> tuple[str, list] | tuple[str, list, str]:
    return (
        history_query,
        [session_id, allowed_sources, developer_id],
    )
