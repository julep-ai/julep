from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for deleting entries with a developer check
delete_entry_query = """
DELETE FROM entries
USING developers
WHERE entries.session_id = $1           -- session_id
    AND developers.developer_id = $2    -- developer_id

RETURNING entries.session_id as session_id;
"""

# Define the raw SQL query for deleting entries with a developer check
delete_entry_relations_query = """
DELETE FROM entry_relations
WHERE entry_relations.session_id = $1 -- session_id
"""

# Define the raw SQL query for deleting entries with a developer check
delete_entry_relations_by_ids_query = """
DELETE FROM entry_relations
WHERE entry_relations.session_id = $1       -- session_id
    AND (entry_relations.head = ANY($2)    -- entry_ids
    OR entry_relations.tail = ANY($2))    -- entry_ids
"""

# Define the raw SQL query for deleting entries by entry_ids with a developer check
delete_entry_by_ids_query = """
DELETE FROM entries
USING developers
WHERE entries.entry_id = ANY($1)        -- entry_ids
    AND developers.developer_id = $2    -- developer_id
    AND entries.session_id = $3         -- session_id

RETURNING entries.entry_id as entry_id;
"""

# Add a session_exists_query similar to create_entries.py
session_exists_query = """
SELECT EXISTS (
    SELECT 1
    FROM sessions
    WHERE session_id = $1
      AND developer_id = $2
);
"""


@rewrap_exceptions(common_db_exceptions("entry", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["session_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@query_metrics("delete_entries_for_session")
@pg_query
@beartype
async def delete_entries_for_session(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]:
    """Delete all entries for a given session."""
    return [
        (session_exists_query, [session_id, developer_id], "fetchrow"),
        (delete_entry_relations_query, [session_id], "fetchmany"),
        (delete_entry_query, [session_id, developer_id], "fetchmany"),
    ]


@rewrap_exceptions(common_db_exceptions("entry", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    transform=lambda d: {
        "id": d["entry_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@query_metrics("delete_entries")
@pg_query
@beartype
async def delete_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    entry_ids: list[UUID],
) -> list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]:
    """Delete specific entries by their IDs.

    Parameters:
        developer_id (UUID): The ID of the developer.
        session_id (UUID): The ID of the session.
        entry_ids (list[UUID]): The IDs of the entries to delete.

    Returns:
        list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]: SQL query and parameters for deleting the entries.
    """
    return [
        (
            session_exists_query,
            [session_id, developer_id],
            "fetchrow",
        ),
        (delete_entry_relations_by_ids_query, [session_id, entry_ids], "fetch"),
        (
            delete_entry_by_ids_query,
            [entry_ids, developer_id, session_id],
            "fetch",
        ),
    ]
