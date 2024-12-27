from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from sqlglot import parse_one

from ...common.protocol.sessions import ChatContext, make_session
from ..utils import (
    pg_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


sql_query = parse_one("""
SELECT * FROM 
(
    SELECT jsonb_agg(u) AS users FROM (
        SELECT 
            session_lookup.participant_id,
            users.user_id AS id,
            users.developer_id,
            users.name,
            users.about,
            users.created_at,
            users.updated_at,
            users.metadata
        FROM session_lookup
        INNER JOIN users ON session_lookup.participant_id = users.user_id
        WHERE
            session_lookup.developer_id = $1 AND
            session_id = $2 AND
            session_lookup.participant_type = 'user'
    ) u
) AS users,
(
    SELECT jsonb_agg(a) AS agents FROM (
        SELECT 
            session_lookup.participant_id,
            agents.agent_id AS id,
            agents.developer_id,
            agents.canonical_name,
            agents.name,
            agents.about,
            agents.instructions,
            agents.model,
            agents.created_at,
            agents.updated_at,
            agents.metadata,
            agents.default_settings
        FROM session_lookup
        INNER JOIN agents ON session_lookup.participant_id = agents.agent_id
        WHERE
            session_lookup.developer_id = $1 AND
            session_id = $2 AND
            session_lookup.participant_type = 'agent'
    ) a
) AS agents,
(
    SELECT to_jsonb(s) AS session FROM (
        SELECT 
            sessions.session_id AS id,
            sessions.developer_id,
            sessions.situation,
            sessions.system_template,
            sessions.created_at,
            sessions.updated_at,
            sessions.metadata,
            sessions.render_templates,
            sessions.token_budget,
            sessions.context_overflow,
            sessions.forward_tool_calls,
            sessions.recall_options
        FROM sessions
        WHERE
            developer_id = $1 AND 
            session_id = $2
        LIMIT 1
    ) s
) AS session,
(
    SELECT jsonb_agg(r) AS toolsets FROM (
        SELECT 
            session_lookup.participant_id, 
            tools.tool_id as id,
            tools.developer_id,
            tools.agent_id,
            tools.task_id,
            tools.type,
            tools.name,
            tools.description,
            tools.spec,
            tools.updated_at,
            tools.created_at
        FROM session_lookup
        INNER JOIN tools ON session_lookup.participant_id = tools.agent_id
        WHERE
            session_lookup.developer_id = $1 AND 
            session_id = $2 AND 
            session_lookup.participant_type = 'agent'
    ) r
) AS toolsets""").sql(pretty=True)


def _transform(d):
    toolsets = {}

    # Default to empty lists when users/agents are not present
    d["users"] = d.get("users") or []
    d["agents"] = d.get("agents") or []

    for tool in d.get("toolsets") or []:
        agent_id = tool["agent_id"]
        if agent_id in toolsets:
            toolsets[agent_id].append(tool)
        else:
            toolsets[agent_id] = [tool]

    transformed_data = {
        **d,
        "session": make_session(
            agents=[a["id"] for a in d.get("agents") or []],
            users=[u["id"] for u in d.get("users") or []],
            **d["session"],
        ),
        "toolsets": [
            {
                "agent_id": agent_id,
                "tools": [
                    {
                        tool["type"]: tool.pop("spec"),
                        **tool,
                    }
                    for tool in tools
                ],
            }
            for agent_id, tools in toolsets.items()
        ],
    }

    return transformed_data


# TODO: implement this part
# @rewrap_exceptions(
#     {
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(
    ChatContext,
    one=True,
    transform=_transform,
)
@pg_query
@beartype
async def prepare_chat_context(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> tuple[str, list]:
    """
    Executes a complex query to retrieve memory context based on session ID.
    """

    return (
        sql_query,
        [developer_id, session_id],
    )
