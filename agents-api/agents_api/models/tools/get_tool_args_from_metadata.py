from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


def tool_args_for_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID,
    tool_type: Literal["integration", "api_call"] = "integration",
    arg_type: Literal["args", "setup"] = "args",
) -> tuple[list[str], dict]:
    agent_id = str(agent_id)
    task_id = str(task_id)

    get_query = f"""
        input[agent_id, task_id] <- [[to_uuid($agent_id), to_uuid($task_id)]]

        ?[values] :=
            input[agent_id, task_id],
            *tasks {{
                task_id,
                metadata: task_metadata,
            }},
            *agents {{
                agent_id,
                metadata: agent_metadata,
            }},
            task_{arg_type} = get(task_metadata, "x-{tool_type}-{arg_type}", {{}}),
            agent_{arg_type} = get(agent_metadata, "x-{tool_type}-{arg_type}", {{}}),

            # Right values overwrite left values
            # See: https://docs.cozodb.org/en/latest/functions.html#Func.Vector.concat
            values = concat(agent_{arg_type}, task_{arg_type}),
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "tasks", task_id=task_id, parents=[("agents", "agent_id")]
        ),
        get_query,
    ]

    return (queries, {"agent_id": agent_id, "task_id": task_id})


def tool_args_for_session(
    *,
    developer_id: UUID,
    session_id: UUID,
    agent_id: UUID,
    arg_type: Literal["args", "setup"] = "args",
    tool_type: Literal["integration", "api_call"] = "integration",
) -> tuple[list[str], dict]:
    session_id = str(session_id)

    get_query = f"""
        input[session_id, agent_id] <- [[to_uuid($session_id), to_uuid($agent_id)]]

        ?[values] :=
            input[session_id, agent_id],
            *sessions {{
                session_id,
                metadata: session_metadata,
            }},
            *agents {{
                agent_id,
                metadata: agent_metadata,
            }},
            session_{arg_type} = get(session_metadata, "x-{tool_type}-{arg_type}", {{}}),
            agent_{arg_type} = get(agent_metadata, "x-{tool_type}-{arg_type}", {{}}),

            # Right values overwrite left values
            # See: https://docs.cozodb.org/en/latest/functions.html#Func.Vector.concat
            values = concat(agent_{arg_type}, session_{arg_type}),
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        get_query,
    ]

    return (queries, {"agent_id": agent_id, "session_id": session_id})


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(dict, transform=lambda x: x["values"], one=True)
@cozo_query
@beartype
def get_tool_args_from_metadata(
    *,
    developer_id: UUID,
    agent_id: UUID,
    session_id: UUID | None = None,
    task_id: UUID | None = None,
    tool_type: Literal["integration", "api_call"] = "integration",
    arg_type: Literal["args", "setup", "headers"] = "args",
) -> tuple[list[str], dict]:
    common: dict = dict(
        developer_id=developer_id,
        agent_id=agent_id,
        tool_type=tool_type,
        arg_type=arg_type,
    )

    match session_id, task_id:
        case (None, task_id) if task_id is not None:
            return tool_args_for_task(
                **common,
                task_id=task_id,
            )

        case (session_id, None) if session_id is not None:
            return tool_args_for_session(
                **common,
                session_id=session_id,
            )

        case (_, _):
            raise ValueError("Either session_id or task_id must be provided")
