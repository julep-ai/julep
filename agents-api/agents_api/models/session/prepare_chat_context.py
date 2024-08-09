from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import make_session
from ...common.protocol.sessions import ChatContext
from ..entry.list_entries import list_entries
from ..tools.list_tools import list_tools
from ..utils import (
    cozo_query,
    make_cozo_json_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)
from .prepare_session_data import prepare_session_data


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
    },
)
@cozo_query
@beartype
def prepare_chat_context(
    *,
    developer_id: UUID,
    agent_id: UUID,
    session_id: UUID,
) -> tuple[list[str], dict]:
    """
    Executes a complex query to retrieve memory context based on session ID.
    """

    session_data_query, sd_vars = prepare_session_data.__wrapped__(
        developer_id=developer_id, session_id=session_id
    )

    # Remove the outer curly braces
    session_data_query = session_data_query.strip()[1:-1]

    session_data_fields = ("session", "agents", "users")

    session_data_query += """
        :create _session_data_json {
            agents: [Json],
            users: [Json],
            session: Json,
        }
    """

    tools_query, t_vars = list_tools.__wrapped__(
        developer_id=developer_id, agent_id=agent_id
    )

    # Remove the outer curly braces
    tools_query = tools_query.strip()[1:-1]

    tools_fields = ("name", "type", "spec")

    tools_query += f"""
        :create _tools {{
            {', '.join(tools_fields)}
        }}
    """

    entries_query, e_vars = list_entries.__wrapped__(
        developer_id=developer_id,
        session_id=session_id,
        allowed_sources=["api_request", "api_response", "summarizer"],
        exclude_relations=["summary_of"],
    )

    # Remove the outer curly braces
    entries_query = entries_query.strip()[1:-1]

    entries_fields = ("source", "role", "name", "content", "token_count", "timestamp")

    entries_query += f"""
        :create _entries {{
            {', '.join(entries_fields)}
        }}
    """

    combine_query = f"""
        tools_json[collect(tool)] :=
            *_tools {{ {', '.join(tools_fields)} }},
            tool = {{ {make_cozo_json_query(tools_fields)} }}

        entries_json[collect(entry)] :=
            *_entries {{ {', '.join(entries_fields)} }},
            entry = {{ {make_cozo_json_query(entries_fields)} }}

        ?[{', '.join(session_data_fields)}, tools, entries] :=
            *_session_data_json {{ {', '.join(session_data_fields)} }},
            tools_json[tools],
            entries_json[entries]
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        session_data_query,
        tools_query,
        entries_query,
        combine_query,
    ]

    return (
        queries,
        {
            "session_id": str(session_id),
            **sd_vars,
            **t_vars,
            **e_vars,
        },
    )
