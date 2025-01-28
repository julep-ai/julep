from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Session, UpdateSessionRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
session_query = """
UPDATE sessions
SET
    situation = $3,
    system_template = $4,
    metadata = $5,
    render_templates = $6,
    token_budget = $7,
    context_overflow = $8,
    forward_tool_calls = $9,
    recall_options = $10
WHERE developer_id = $1 AND session_id = $2
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("session", ["update"]))
@wrap_in_class(
    Session,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["session_id"],
    },
)
@increase_counter("update_session")
@pg_query
@beartype
async def update_session(
    *,
    developer_id: UUID,
    session_id: UUID,
    data: UpdateSessionRequest,
) -> list[tuple[str, list]]:
    """
    Constructs SQL queries to update a session and its participant lookups.

    Args:
        developer_id (UUID): The developer's UUID
        session_id (UUID): The session's UUID
        data (UpdateSessionRequest): Session update data

    Returns:
        list[tuple[str, list]]: List of SQL queries and their parameters
    """
    # Prepare session parameters
    session_params = [
        developer_id,  # $1
        session_id,  # $2
        data.situation,  # $3
        data.system_template,  # $4
        data.metadata or {},  # $5
        data.render_templates,  # $6
        data.token_budget,  # $7
        data.context_overflow,  # $8
        data.forward_tool_calls,  # $9
        data.recall_options.model_dump() if data.recall_options else {},  # $10
    ]

    return [
        (session_query, session_params),
    ]
