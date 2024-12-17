from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateSessionRequest
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL queries
session_query = parse_one("""
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
WHERE 
    developer_id = $1 
    AND session_id = $2
RETURNING *;
""").sql(pretty=True)

lookup_query = parse_one("""
WITH deleted_lookups AS (
    DELETE FROM session_lookup
    WHERE developer_id = $1 AND session_id = $2
)
INSERT INTO session_lookup (
    developer_id,
    session_id,
    participant_type,
    participant_id
)
SELECT 
    $1 as developer_id,
    $2 as session_id,
    unnest($3::participant_type[]) as participant_type,
    unnest($4::uuid[]) as participant_id;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or participant does not exist.",
        ),
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="Session not found",
        ),
    }
)
@wrap_in_class(ResourceUpdatedResponse, one=True)
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
    participant_types = (
        ["user"] * len(users) + ["agent"] * len(agents)
    )
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
    lookup_params = [
        developer_id,  # $1
        session_id,  # $2
        participant_types,  # $3
        participant_ids,  # $4
    ]

    return [
        (session_query, session_params),
        (lookup_query, lookup_params),
    ]
