from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateEntryRequest, Entry
from ...common.utils.datetime import utcnow
from ...common.utils.messages import content_to_json
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating entries with a developer check
raw_query = """
INSERT INTO entries (
    session_id,
    entry_id,
    source,
    role,
    event_type,
    name,
    content,
    tool_call_id,
    tool_calls,
    model,
    token_count,
    created_at,
    timestamp
)
SELECT
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
FROM
    developers
WHERE
    developer_id = $14
RETURNING *;
"""

# Parse and optimize the query
query = optimize(
    parse_one(raw_query),
    schema={
        "entries": {
            "session_id": "UUID",
            "entry_id": "UUID",
            "source": "TEXT",
            "role": "chat_role",
            "event_type": "TEXT",
            "name": "TEXT",
            "content": "JSONB[]",
            "tool_call_id": "TEXT",
            "tool_calls": "JSONB[]",
            "model": "TEXT",
            "token_count": "INTEGER",
            "created_at": "TIMESTAMP",
            "timestamp": "TIMESTAMP",
        }
    },
).sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(HTTPException, status_code=400),
        asyncpg.UniqueViolationError: partialclass(HTTPException, status_code=409),
    }
)
@wrap_in_class(Entry)
@increase_counter("create_entries")
@pg_query
@beartype
def create_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    data: list[CreateEntryRequest],
    mark_session_as_updated: bool = True,
) -> tuple[str, list]:
    data_dicts = [item.model_dump(mode="json") for item in data]

    params = [
        (
            session_id,
            item.pop("id", None) or str(uuid7()),
            item.get("source"),
            item.get("role"),
            item.get("event_type") or "message.create",
            item.get("name"),
            content_to_json(item.get("content") or []),
            item.get("tool_call_id"),
            item.get("tool_calls") or [],
            item.get("model"),
            item.get("token_count"),
            (item.get("created_at") or utcnow()).timestamp(),
            utcnow().timestamp(),
            developer_id
        )
        for item in data_dicts
    ]

    return (
        query,
        params,
    )
