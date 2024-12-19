from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for deleting entries with a developer check
delete_entry_query = parse_one("""
DELETE FROM entries
USING developers
WHERE entries.session_id = $1           -- session_id
    AND developers.developer_id = $2    -- developer_id

RETURNING entries.session_id as session_id;
""").sql(pretty=True)

# Define the raw SQL query for deleting entries with a developer check
delete_entry_relations_query = parse_one("""
DELETE FROM entry_relations
WHERE entry_relations.session_id = $1 -- session_id
""").sql(pretty=True)

# Define the raw SQL query for deleting entries with a developer check
delete_entry_relations_by_ids_query = parse_one("""
DELETE FROM entry_relations
WHERE entry_relations.session_id = $1       -- session_id
    AND (entry_relations.head = ANY($2)    -- entry_ids
    OR entry_relations.tail = ANY($2))    -- entry_ids
""").sql(pretty=True)

# Define the raw SQL query for deleting entries by entry_ids with a developer check
delete_entry_by_ids_query = parse_one("""
DELETE FROM entries
USING developers
WHERE entries.entry_id = ANY($1)        -- entry_ids
    AND developers.developer_id = $2    -- developer_id
    AND entries.session_id = $3         -- session_id

RETURNING entries.entry_id as entry_id;
""").sql(pretty=True)

# Add a session_exists_query similar to create_entries.py
session_exists_query = """
SELECT EXISTS (
    SELECT 1
    FROM sessions
    WHERE session_id = $1
      AND developer_id = $2
);
"""


# @rewrap_exceptions(
#     {
#         asyncpg.ForeignKeyViolationError: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="The specified session or developer does not exist.",
#         ),
#         asyncpg.UniqueViolationError: partialclass(
#             HTTPException,
#             status_code=409,
#             detail="The specified session has already been deleted.",
#         ),
#     }
# )
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["session_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@increase_counter("delete_entries_for_session")
@pg_query
@beartype
async def delete_entries_for_session(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> list[tuple[str, list, Literal["fetch", "fetchmany"]]]:
    """Delete all entries for a given session."""
    return [
        (session_exists_query, [session_id, developer_id], "fetch"),
        (delete_entry_relations_query, [session_id], "fetchmany"),
        (delete_entry_query, [session_id, developer_id], "fetchmany"),
    ]


# @rewrap_exceptions(
#     {
#         asyncpg.ForeignKeyViolationError: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="The specified entries, session, or developer does not exist.",
#         ),
#         asyncpg.UniqueViolationError: partialclass(
#             HTTPException,
#             status_code=409,
#             detail="One or more specified entries have already been deleted.",
#         ),
#     }
# )
@wrap_in_class(
    ResourceDeletedResponse,
    transform=lambda d: {
        "id": d["entry_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@increase_counter("delete_entries")
@pg_query
@beartype
async def delete_entries(
    *, developer_id: UUID, session_id: UUID, entry_ids: list[UUID]
) -> list[tuple[str, list, Literal["fetch", "fetchmany"]]]:
    """Delete specific entries by their IDs."""
    return [
        (session_exists_query, [session_id, developer_id], "fetch"),
        (delete_entry_relations_by_ids_query, [session_id, entry_ids], "fetchmany"),
        (delete_entry_by_ids_query, [entry_ids, developer_id, session_id], "fetchmany"),
    ]
