from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...common.protocol.sessions import ChatContext, make_session
from ..session.prepare_session_data import prepare_session_data
from ..utils import (
    cozo_query,
    fix_uuid_if_present,
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
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ChatContext,
    one=True,
    transform=lambda d: {
        **d,
        "session": make_session(
            agents=[a["id"] for a in d["agents"]],
            users=[u["id"] for u in d["users"]],
            **d["session"],
        ),
        "toolsets": [
            {**ts, "tools": [*map(fix_uuid_if_present, ts["tools"])]}
            for ts in d["toolsets"]
        ],
    },
)
@cozo_query
@beartype
def prepare_chat_context(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> tuple[list[str], dict]:
    """
    Executes a complex query to retrieve memory context based on session ID.
    """

    [*_, session_data_query], sd_vars = prepare_session_data.__wrapped__(
        developer_id=developer_id, session_id=session_id
    )

    session_data_fields = ("session", "agents", "users")

    session_data_query += """
        :create _session_data_json {
            agents: [Json],
            users: [Json],
            session: Json,
        }
    """

    toolsets_query = """
    input[session_id] <- [[to_uuid($session_id)]]

    tools_by_agent[agent_id, collect(tool)] :=
        input[session_id],
        *session_lookup{
            session_id,
            participant_id: agent_id,
            participant_type: "agent",
        },

        *tools { agent_id, tool_id, name, type, spec, updated_at, created_at },
        tool = {
            "id": tool_id,
            "name": name,
            "type": type,
            "spec": spec,
            "updated_at": updated_at,
            "created_at": created_at,
        }

    agent_toolsets[collect(toolset)] :=
        tools_by_agent[agent_id, tools],
        toolset = {
            "agent_id": agent_id,
            "tools": tools,
        }

    ?[toolsets] :=
        agent_toolsets[toolsets]

    :create _toolsets_json {
        toolsets: [Json],
    }
    """

    combine_query = f"""
        ?[{', '.join(session_data_fields)}, toolsets] :=
            *_session_data_json {{ {', '.join(session_data_fields)} }},
            *_toolsets_json {{ toolsets }}
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        session_data_query,
        toolsets_query,
        combine_query,
    ]

    return (
        queries,
        {
            "session_id": str(session_id),
            **sd_vars,
        },
    )
