"""SQL query to fetch agents for a given session."""

from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Agent
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

query = """
SELECT
    a.agent_id,
    a.developer_id,
    a.name,
    a.canonical_name,
    a.about,
    a.instructions,
    a.model,
    a.metadata,
    a.default_settings,
    a.default_system_template,
    a.created_at,
    a.updated_at,
    p.canonical_name AS project
FROM session_lookup sl
JOIN agents a ON sl.participant_id = a.agent_id
    AND sl.developer_id = a.developer_id
LEFT JOIN project_agents pa ON a.agent_id = pa.agent_id
    AND a.developer_id = pa.developer_id
LEFT JOIN projects p ON pa.project_id = p.project_id
    AND pa.developer_id = p.developer_id
WHERE sl.developer_id = $1
  AND sl.session_id = $2
  AND sl.participant_type = 'agent';
"""


@rewrap_exceptions(common_db_exceptions("session", ["get_agents"]))
@wrap_in_class(Agent, transform=lambda d: {**d, "id": d["agent_id"]})
@query_metrics("get_session_agents")
@pg_query
@beartype
async def get_session_agents(*, developer_id: UUID, session_id: UUID) -> tuple[str, list]:
    """Return SQL query to retrieve agents of a session."""

    return (
        query,
        [developer_id, session_id],
    )
