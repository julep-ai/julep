from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import History
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for getting history with a developer check and relations
history_query = """
WITH collected_entries AS (
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
        e.tokenizer,
        s.created_at AS session_created_at
    FROM entries e
    JOIN sessions s ON s.session_id = e.session_id
        AND s.session_id = $1
        AND s.developer_id = $3
    WHERE e.source = ANY($2)
        AND e.created_at >= s.created_at
),
collected_relations AS (
    SELECT
        er.head,
        er.relation,
        er.tail
    FROM entry_relations er
    WHERE er.session_id = $1
)
SELECT
    (SELECT json_agg(e) FROM collected_entries e) AS entries,
    (SELECT json_agg(r) FROM collected_relations r) AS relations,
    (SELECT session_created_at FROM collected_entries LIMIT 1) AS created_at,
    $1::uuid AS session_id
"""


def _transform(row):
    return {
        "entries": [
            {
                **entry,
            }
            for entry in (row["entries"] or [])
        ],
        "relations": [
            {
                "head": r["head"],
                "relation": r["relation"],
                "tail": r["tail"],
            }
            for r in (row["relations"] or [])
        ],
        "session_id": row["session_id"],
        "created_at": row["created_at"] or utcnow(),
    }


@rewrap_exceptions(common_db_exceptions("history", ["get"]))
@wrap_in_class(
    History,
    one=True,
    transform=_transform,
)
@pg_query
@beartype
async def get_history(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
) -> tuple[str, list] | tuple[str, list, str]:
    """
    Get session history.

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
