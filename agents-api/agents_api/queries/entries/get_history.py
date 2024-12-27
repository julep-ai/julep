import json
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import History
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for getting history with a developer check and relations
history_query = """
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
    $1::uuid AS session_id
"""


@rewrap_exceptions(common_db_exceptions("history", ["get"]))
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
    """Get the history of a session.

    Parameters:
        developer_id (UUID): The ID of the developer.
        session_id (UUID): The ID of the session.
        allowed_sources (list[str]): The sources to include in the history.

    Returns:
        tuple[str, list] | tuple[str, list, str]: SQL query and parameters for getting the history.
    """
    return (
        history_query,
        [session_id, allowed_sources, developer_id],
    )
