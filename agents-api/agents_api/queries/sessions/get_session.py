"""This module contains functions for retrieving session data from the PostgreSQL database."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Session
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
query = """
WITH session_participants AS (
    SELECT
        sl.session_id,
        array_agg(sl.participant_id) FILTER (WHERE sl.participant_type = 'agent') as agents,
        array_agg(sl.participant_id) FILTER (WHERE sl.participant_type = 'user') as users
    FROM session_lookup sl
    WHERE sl.developer_id = $1 AND sl.session_id = $2
    GROUP BY sl.session_id
)
SELECT
    s.session_id as id,
    s.developer_id,
    s.situation,
    s.system_template,
    s.metadata,
    s.render_templates,
    s.token_budget,
    s.context_overflow,
    s.forward_tool_calls,
    s.recall_options,
    s.created_at,
    s.updated_at,
    sp.agents,
    sp.users
FROM sessions s
LEFT JOIN session_participants sp ON s.session_id = sp.session_id
WHERE s.developer_id = $1 AND s.session_id = $2;
"""


@rewrap_exceptions(common_db_exceptions("session", ["get"]))
@wrap_in_class(
    Session,
    one=True,
    transform=lambda d: {
        **d,
        "recall_options": None if d["recall_options"] == {} else d["recall_options"],
    },
)
@query_metrics("get_session")
@pg_query
@beartype
async def get_session(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> tuple[str, list]:
    """
    Constructs SQL query to retrieve a session and its participants.

    Args:
        developer_id (UUID): The developer's UUID
        session_id (UUID): The session's UUID

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    return (
        query,
        [developer_id, session_id],
    )
