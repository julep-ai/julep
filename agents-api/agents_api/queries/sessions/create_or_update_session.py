from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import (
    CreateOrUpdateSessionRequest,
    ResourceUpdatedResponse,
)
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
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
ON CONFLICT (developer_id, session_id) DO UPDATE
SET
    situation = EXCLUDED.situation,
    system_template = EXCLUDED.system_template,
    metadata = EXCLUDED.metadata,
    render_templates = EXCLUDED.render_templates,
    token_budget = EXCLUDED.token_budget,
    context_overflow = EXCLUDED.context_overflow,
    forward_tool_calls = EXCLUDED.forward_tool_calls,
    recall_options = EXCLUDED.recall_options
RETURNING *;
"""

lookup_query = """
INSERT INTO session_lookup (
    developer_id,
    session_id,
    participant_type,
    participant_id
)
VALUES ($1, $2, $3, $4)
ON CONFLICT (developer_id, session_id, participant_type, participant_id) DO NOTHING;
"""


@rewrap_exceptions(common_db_exceptions("session", ["create", "update"]))
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["session_id"], "updated_at": d["updated_at"]},
)
@increase_counter("create_or_update_session")
@pg_query(return_index=0)
@beartype
async def create_or_update_session(
    *,
    developer_id: UUID,
    session_id: UUID,
    data: CreateOrUpdateSessionRequest,
) -> list[tuple[str, list] | tuple[str, list, str]]:
    """
    Constructs SQL queries to create or update a session and its participant lookups.

    Args:
        developer_id (UUID): The developer's UUID
        session_id (UUID): The session's UUID
        data (CreateOrUpdateSessionRequest): Session data to insert or update

    Returns:
        list[tuple[str, list]]: List of SQL queries and their parameters
    """
    # Handle participants
    users = data.users or ([data.user] if data.user else [])
    agents = data.agents or ([data.agent] if data.agent else [])

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
        data.recall_options or {},  # $10
    ]

    # Prepare lookup parameters
    lookup_params = []
    for participant_type, participant_id in zip(participant_types, participant_ids):
        lookup_params.append([developer_id, session_id, participant_type, participant_id])

    return [
        (session_query, session_params, "fetch"),
        (lookup_query, lookup_params, "fetchmany"),
    ]
