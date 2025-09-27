"""Database query to create a new chat session for a developer."""
# AIDEV-NOTE: Inserts a new session row and returns it with generated ID.

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateSessionRequest, Session
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL queries
session_query = """
INSERT INTO sessions (
    developer_id,
    session_id,
    situation,
    system_template,
    metadata,
    render_templates,
    token_budget,
    context_overflow,
    forward_tool_calls,
    recall_options
)
VALUES (
    $1, -- developer_id
    $2, -- session_id
    $3, -- situation
    $4, -- system_template
    $5, -- metadata
    $6, -- render_templates
    $7, -- token_budget
    $8, -- context_overflow
    $9, -- forward_tool_calls
    $10 -- recall_options
)
RETURNING *;
"""

lookup_query = """
INSERT INTO session_lookup (
    developer_id,
    session_id,
    participant_type,
    participant_id
)
VALUES ($1, $2, $3, $4);
"""


@rewrap_exceptions(common_db_exceptions("session", ["create"]))
@wrap_in_class(
    Session,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["session_id"],
    },
)
@query_metrics("create_session")
@pg_query(return_index=0)
@beartype
async def create_session(
    *,
    developer_id: UUID,
    session_id: UUID | None = None,
    data: CreateSessionRequest,
) -> list[tuple[str, list] | tuple[str, list, str]]:
    """
    Constructs SQL queries to create a new session and its participant lookups.

    Args:
        developer_id (UUID): The developer's UUID
        session_id (UUID): The session's UUID
        data (CreateSessionRequest): Session creation data

    Returns:
        list[tuple[str, list] | tuple[str, list, str]]: SQL queries and their parameters
    """
    # Handle participants
    users = data.users or ([data.user] if data.user else [])
    agents = data.agents or ([data.agent] if data.agent else [])
    session_id = session_id or uuid7()

    if not agents:
        raise HTTPException(
            status_code=400,
            detail="At least one agent must be provided",
        )

    if data.agent and data.agents:
        raise HTTPException(
            status_code=400,
            detail="Only one of 'agent' or 'agents' should be provided",
        )

    # Prepare participant arrays for lookup query
    participant_types = ["user"] * len(users) + ["agent"] * len(agents)
    participant_ids = [str(u) for u in users] + [str(a) for a in agents]

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

    # Prepare lookup parameters as a list of parameter lists
    lookup_params = []
    for ptype, pid in zip(participant_types, participant_ids):
        lookup_params.append([developer_id, session_id, ptype, pid])

    return [
        (session_query, session_params, "fetch"),
        (lookup_query, lookup_params, "fetchmany"),
    ]
