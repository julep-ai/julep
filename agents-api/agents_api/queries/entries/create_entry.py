from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateEntryRequest, Entry, Relation
from ...common.utils.datetime import utcnow
from ...common.utils.messages import content_to_json
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating entries with a developer check
entry_query = ("""
WITH data AS (
    SELECT
        unnest($1::uuid[]) AS session_id,
        unnest($2::uuid[]) AS entry_id,
        unnest($3::text[]) AS source,
        unnest($4::text[])::chat_role AS role,
        unnest($5::text[]) AS event_type,
        unnest($6::text[]) AS name,
        array[unnest($7::jsonb[])] AS content,
        unnest($8::text[]) AS tool_call_id,
        array[unnest($9::jsonb[])] AS tool_calls,
        unnest($10::text[]) AS model,
        unnest($11::int[]) AS token_count,
        unnest($12::timestamptz[]) AS created_at,
        unnest($13::timestamptz[]) AS timestamp
)
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
    d.session_id,
    d.entry_id,
    d.source,
    d.role,
    d.event_type,
    d.name,
    d.content,
    d.tool_call_id,
    d.tool_calls,
    d.model,
    d.token_count,
    d.created_at,
    d.timestamp
FROM
    data d
JOIN
    developers ON developers.developer_id = $14
RETURNING *;
""")

# Define the raw SQL query for creating entry relations
entry_relation_query = ("""
WITH data AS (
    SELECT
        unnest($1::uuid[]) AS session_id,
        unnest($2::uuid[]) AS head,
        unnest($3::text[]) AS relation,
        unnest($4::uuid[]) AS tail,
        unnest($5::boolean[]) AS is_leaf
)
INSERT INTO entry_relations (
    session_id,
    head,
    relation,
    tail,
    is_leaf
)
SELECT
    d.session_id,
    d.head,
    d.relation,
    d.tail,
    d.is_leaf
FROM
    data d
JOIN
    developers ON developers.developer_id = $6
RETURNING *;
""")


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
@wrap_in_class(
    Entry,
    transform=lambda d: {
        "id": UUID(d.pop("entry_id")),
        **d,
    },
)
@increase_counter("create_entries")
@pg_query
@beartype
async def create_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    data: list[CreateEntryRequest],
) -> tuple[str, list]:
    # Convert the data to a list of dictionaries
    data_dicts = [item.model_dump(mode="json") for item in data]

    # Prepare the parameters for the query
    params = [
        [session_id] * len(data_dicts),  # $1
        [item.pop("id", None) or str(uuid7()) for item in data_dicts],  # $2
        [item.get("source") for item in data_dicts],  # $3
        [item.get("role") for item in data_dicts],  # $4
        [item.get("event_type") or "message.create" for item in data_dicts],  # $5
        [item.get("name") for item in data_dicts],  # $6
        [content_to_json(item.get("content") or {}) for item in data_dicts],  # $7
        [item.get("tool_call_id") for item in data_dicts],  # $8
        [content_to_json(item.get("tool_calls") or {}) for item in data_dicts],  # $9
        [item.get("modelname") for item in data_dicts],  # $10
        [item.get("token_count") for item in data_dicts],  # $11
        [item.get("created_at") or utcnow() for item in data_dicts],  # $12
        [utcnow() for _ in data_dicts],  # $13
        developer_id,  # $14
    ]

    return (
        entry_query,
        params,
    )


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
    }
)
@wrap_in_class(Relation)
@increase_counter("add_entry_relations")
@pg_query
@beartype
async def add_entry_relations(
    *,
    developer_id: UUID,
    data: list[Relation],
) -> tuple[str, list]:
    # Convert the data to a list of dictionaries
    data_dicts = [item.model_dump(mode="json") for item in data]

    # Prepare the parameters for the query
    params = [
        [item.get("session_id") for item in data_dicts],  # $1
        [item.get("head") for item in data_dicts],  # $2
        [item.get("relation") for item in data_dicts],  # $3
        [item.get("tail") for item in data_dicts],  # $4
        [item.get("is_leaf", False) for item in data_dicts],  # $5
        developer_id,  # $6
    ]

    return (
        entry_relation_query,
        params,
    )
