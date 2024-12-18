from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import CreateSessionRequest, Session
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL queries
session_query = parse_one("""
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
""").sql(pretty=True)

lookup_query = parse_one("""
INSERT INTO session_lookup (
    developer_id,
    session_id,
    participant_type,
    participant_id
)
VALUES ($1, $2, $3, $4);
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or participant does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="A session with this ID already exists.",
        ),
    }
)
@wrap_in_class(Session, transform=lambda d: {**d, "id": d["session_id"]})
@increase_counter("create_session")
@pg_query
@beartype
async def create_session(
    *,
    developer_id: UUID,
    session_id: UUID,
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

    # Prepare lookup parameters as a list of parameter lists
    lookup_params = []
    for ptype, pid in zip(participant_types, participant_ids):
        lookup_params.append([developer_id, session_id, ptype, pid])

    print("*" * 100)
    print(lookup_params)
    print("*" * 100)
    return [
        (session_query, session_params),
        (lookup_query, lookup_params, "fetchmany"),
    ]
