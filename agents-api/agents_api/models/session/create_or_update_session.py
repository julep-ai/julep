from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    CreateOrUpdateSessionRequest,
    ResourceUpdatedResponse,
)
from ...common.utils.cozo import cozo_process_mutate_data
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
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {
        "id": d["session_id"],
        "updated_at": d.pop("updated_at")[0],
        "jobs": [],
        **d,
    },
)
@cozo_query
@beartype
def create_or_update_session(
    *,
    session_id: UUID,
    developer_id: UUID,
    data: CreateOrUpdateSessionRequest,
) -> tuple[list[str], dict]:
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
    clear_lookup_query = """
        input[session_id] <- [[$session_id]]
        ?[session_id, participant_id, participant_type] :=
            input[session_id],
            *session_lookup {
                session_id,
                participant_type,
                participant_id,
            },

        :delete session_lookup {
            session_id,
            participant_type,
            participant_id,
        }
    """

    lookup_query = """
        # This section creates a new session lookup to ensure uniqueness and manage session metadata.
        session[session_id] <- [[$session_id]]
        participants[participant_type, participant_id] <- $participants
        ?[session_id, participant_id, participant_type] :=
            session[session_id],
            participants[participant_type, participant_id],

        :put session_lookup {
            session_id,
            participant_id,
            participant_type,
        }
    """

    session_update_cols, session_update_vals = cozo_process_mutate_data(
        {k: v for k, v in session_data.items() if v is not None}
    )

    # Construct the datalog query for creating or updating session information.
    update_query = f"""
        input[{session_update_cols}] <- $session_update_vals
        ids[session_id, developer_id] <- [[to_uuid($session_id), to_uuid($developer_id)]]
        
        ?[{session_update_cols}, session_id, developer_id] :=
            input[{session_update_cols}],
            ids[session_id, developer_id],

        :put sessions {{
           {session_update_cols}, session_id, developer_id 
        }}

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
        clear_lookup_query,
        lookup_query,
        update_query,
    ]

    return (
        queries,
        {
            "session_update_vals": session_update_vals,
            "session_id": str(session_id),
            "developer_id": str(developer_id),
            "participants": participants,
        },
    )
