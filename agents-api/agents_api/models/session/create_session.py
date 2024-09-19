"""
This module contains the functionality for creating a new session in the 'cozodb' database.
It constructs and executes a datalog query to insert session data.
"""

from typing import Any, TypeVar
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateSessionRequest, Session
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        AssertionError: partialclass(HTTPException, status_code=400),
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    Session,
    one=True,
    transform=lambda d: {
        "id": UUID(d.pop("session_id")),
        "updated_at": (d.pop("updated_at")[0]),
        **d,
    },
    _kind="inserted",
)
@cozo_query
@beartype
def create_session(
    *,
    developer_id: UUID,
    session_id: UUID | None = None,
    data: CreateSessionRequest,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to create a new session in the database.
    """

    session_id = session_id or uuid4()

    data.metadata = data.metadata or {}
    session_data = data.model_dump()

    user = session_data.pop("user")
    agent = session_data.pop("agent")
    users = session_data.pop("users")
    agents = session_data.pop("agents")

    # Only one of agent or agents should be provided.
    if agent and agents:
        raise ValueError("Only one of 'agent' or 'agents' should be provided.")

    agents = agents or ([agent] if agent else [])
    assert len(agents) > 0, "At least one agent must be provided."

    # Users are zero or more, so we default to an empty list if not provided.
    if not (user or users):
        users = []

    else:
        users = users or [user]

    participants = [
        *[("user", str(user)) for user in users],
        *[("agent", str(agent)) for agent in agents],
    ]

    # Construct the datalog query for creating a new session and its lookup.
    lookup_query = """
        # This section creates a new session lookup to ensure uniqueness and manage session metadata.
        session[session_id] <- [[$session_id]]
        participants[participant_type, participant_id] <- $participants
        ?[session_id, participant_id, participant_type] :=
            session[session_id],
            participants[participant_type, participant_id],

        :insert session_lookup {
            session_id,
            participant_id,
            participant_type,
        }
    """

    create_query = """
        # Insert the new session data into the 'session' table with the specified columns.
        ?[session_id, developer_id, situation, metadata, render_templates, token_budget, context_overflow] <- [[
            $session_id,
            $developer_id,
            $situation,
            $metadata,
            $render_templates,
            $token_budget,
            $context_overflow,
        ]]

        :insert sessions {
            developer_id,
            session_id,
            situation,
            metadata,
            render_templates,
            token_budget,
            context_overflow,
        }
        # Specify the data to return after the query execution, typically the newly created session's ID.
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        *[
            verify_developer_owns_resource_query(
                developer_id,
                f"{participant_type}s",
                **{f"{participant_type}_id": participant_id},
            )
            for participant_type, participant_id in participants
        ],
        lookup_query,
        create_query,
    ]

    # Execute the constructed query with the provided parameters and return the result.
    return (
        queries,
        {
            "session_id": str(session_id),
            "developer_id": str(developer_id),
            "participants": participants,
            **session_data,
        },
    )
