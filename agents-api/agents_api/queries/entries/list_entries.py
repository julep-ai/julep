from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Entry
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query for checking if the session exists
session_exists_query = """
SELECT EXISTS (
    SELECT 1 FROM sessions
    WHERE session_id = $1 AND developer_id = $2
) AS exists;
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
    e.model,
    e.tokenizer
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


@rewrap_exceptions(common_db_exceptions("entry", ["list"]))
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
) -> list[tuple[str, list] | tuple[str, list, str]]:
    """List entries in a session.

    Parameters:
        developer_id (UUID): The ID of the developer.
        session_id (UUID): The ID of the session.
        allowed_sources (list[str]): The sources to include in the history.
        limit (int): The number of entries to return.
        offset (int): The number of entries to skip.
        sort_by (Literal["created_at", "timestamp"]): The field to sort by.
        direction (Literal["asc", "desc"]): The direction to sort by.
        exclude_relations (list[str]): The relations to exclude.

    Returns:
        tuple[str, list] | tuple[str, list, str]: SQL query and parameters for listing the entries.
    """
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
            "fetchrow",
        ),
        (
            query,
            entry_params,
            "fetch",
        ),
    ]
