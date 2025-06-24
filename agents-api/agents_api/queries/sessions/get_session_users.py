"""SQL query to fetch users for a given session."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
SELECT
    u.user_id,
    u.developer_id,
    u.name,
    u.about,
    u.metadata,
    u.created_at,
    u.updated_at,
    p.canonical_name AS project
FROM session_lookup sl
JOIN users u ON sl.participant_id = u.user_id
    AND sl.developer_id = u.developer_id
LEFT JOIN project_users pu ON u.user_id = pu.user_id
    AND u.developer_id = pu.developer_id
LEFT JOIN projects p ON pu.project_id = p.project_id
    AND pu.developer_id = p.developer_id
WHERE sl.developer_id = $1
  AND sl.session_id = $2
  AND sl.participant_type = 'user';
"""


@rewrap_exceptions(common_db_exceptions("session", ["get_users"]))
@wrap_in_class(User, transform=lambda d: {**d, "id": d["user_id"]})
@query_metrics("get_session_users")
@pg_query
@beartype
async def get_session_users(*, developer_id: UUID, session_id: UUID) -> tuple[str, list]:
    """Return SQL query to retrieve users of a session."""

    return (
        query,
        [developer_id, session_id],
    )
