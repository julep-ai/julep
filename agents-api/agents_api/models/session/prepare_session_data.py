from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import make_session
from ...common.protocol.sessions import SessionData
from ...common.utils.cozo import uuid_int_list_to_uuid4 as fix_uuid
from ..utils import (
    cozo_query,
    fix_uuid_list,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    SessionData,
    one=True,
    transform=lambda d: {
        "agents": fix_uuid_list(d["agents"]),
        "users": fix_uuid_list(d["users"]),
        "session": make_session(
            agents=[fix_uuid(a["id"]) for a in d["agents"]],
            users=[fix_uuid(u["id"]) for u in d["users"]],
            id=fix_uuid(d["session"].pop("id")),
            **d["session"],
        ),
    },
)
@cozo_query
@beartype
def prepare_session_data(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> tuple[str, dict]:
    """Constructs and executes a datalog query to retrieve session data from the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        session_id (UUID): The session's unique identifier.
    """
    session_id = str(session_id)
    developer_id = str(developer_id)

    # This query retrieves session information by using `input` to pass parameters,
    get_query = """
    input[session_id] <- [[
        to_uuid($session_id),
    ]]

    participants[collect(participant_id), participant_type] :=
        input[session_id],
        *session_lookup{
            session_id,
            participant_id,
            participant_type,
        }

    agents[agent_ids] := participants[agent_ids, "agent"]

    # We have to do this dance because users can be zero or more
    users[user_ids] :=
        participants[user_ids, "user"]

    users[user_ids] :=
        not participants[_, "user"],
        user_ids = []

    settings_data[agent_id, settings] :=
        *agent_default_settings {
            agent_id,
            frequency_penalty,
            presence_penalty,
            length_penalty,
            repetition_penalty,
            top_p,
            temperature,
            min_p,
            preset,
        },
        settings = {
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "length_penalty": length_penalty,
            "repetition_penalty": repetition_penalty,
            "top_p": top_p,
            "temperature": temperature,
            "min_p": min_p,
            "preset": preset,
        }

    agent_data[collect(record)] :=
        agents[agent_ids],
        agent_id in agent_ids,
        *agents{
            agent_id,
            model,
            name,
            about,
            created_at,
            updated_at,
            metadata,
            instructions,
        },
        settings_data[agent_id, default_settings],
        record = {
            "id":         agent_id,
            "name":       name,
            "model":      model,
            "about":      about,
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata":   metadata,
            "default_settings":  default_settings,
            "instructions":      instructions,
        }

    user_data[collect(record)] :=
        users[user_ids],
        user_id in user_ids,
        *users{
            user_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        },
        record = {
            "id":         user_id,
            "name":       name,
            "about":      about,
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata":   metadata,
        }

    session_data[record] :=
        input[session_id],
        *sessions{
            session_id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata,
            render_templates,
            token_budget,
            context_overflow,
            @ "NOW"
        },
        updated_at = to_int(validity),
        record = {
            "id":               session_id,
            "situation":        situation,
            "summary":          summary,
            "created_at":       created_at,
            "updated_at":       updated_at,
            "metadata":         metadata,
            "render_templates": render_templates,
            "token_budget":     token_budget,
            "context_overflow": context_overflow,
        }

    ?[
        agents,
        users,
        session,
    ] :=
        session_data[session],
        user_data[users],
        agent_data[agents]
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        get_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (
        query,
        {"developer_id": developer_id, "session_id": session_id},
    )
