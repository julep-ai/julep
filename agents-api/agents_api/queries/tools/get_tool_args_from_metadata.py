from typing import Literal
from uuid import UUID

import sqlvalidator
from beartype import beartype

from sqlglot import parse_one
from ..utils import (
    pg_query,
    wrap_in_class,
    rewrap_exceptions,
    partialclass,
)

# Define the raw SQL query for getting tool args from metadata
tools_args_for_task_query = parse_one("""
SELECT COALESCE(agents_md || tasks_md, agents_md, tasks_md, '{}') as values FROM (
    SELECT
        CASE WHEN $3 = 'x-integrations-args' then metadata->'x-integrations-args'
        WHEN $3 = 'x-api_call-args' then metadata->'x-api_call-args'
        WHEN $3 = 'x-integrations-setup' then metadata->'x-integrations-setup'
        WHEN $3 = 'x-api_call-setup' then metadata->'x-api_call-setup' END AS agents_md
    FROM agents
    WHERE agent_id = $1 AND developer_id = $4 LIMIT 1
) AS agents_md,
(
    SELECT
        CASE WHEN $3 = 'x-integrations-args' then metadata->'x-integrations-args'
        WHEN $3 = 'x-api_call-args' then metadata->'x-api_call-args'
        WHEN $3 = 'x-integrations-setup' then metadata->'x-integrations-setup'
        WHEN $3 = 'x-api_call-setup' then metadata->'x-api_call-setup' END AS tasks_md
    FROM tasks
    WHERE task_id = $2 AND developer_id = $4 LIMIT 1
) AS tasks_md""").sql(pretty=True)

# Define the raw SQL query for getting tool args from metadata for a session
tool_args_for_session_query = parse_one("""SELECT COALESCE(agents_md || sessions_md, agents_md, sessions_md, '{}') as values FROM (
    SELECT
        CASE WHEN $3 = 'x-integrations-args' then metadata->'x-integrations-args'
        WHEN $3 = 'x-api_call-args' then metadata->'x-api_call-args'
        WHEN $3 = 'x-integrations-setup' then metadata->'x-integrations-setup'
        WHEN $3 = 'x-api_call-setup' then metadata->'x-api_call-setup' END AS agents_md
    FROM agents
    WHERE agent_id = $1 AND developer_id = $4 LIMIT 1
) AS agents_md,
(
    SELECT
        CASE WHEN $3 = 'x-integrations-args' then metadata->'x-integrations-args'
        WHEN $3 = 'x-api_call-args' then metadata->'x-api_call-args'
        WHEN $3 = 'x-integrations-setup' then metadata->'x-integrations-setup'
        WHEN $3 = 'x-api_call-setup' then metadata->'x-api_call-setup' END AS tasks_md
    FROM sessions
    WHERE session_id = $2 AND developer_id = $4 LIMIT 1
) AS sessions_md""").sql(pretty=True)



# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(dict, transform=lambda x: x["values"], one=True)
@pg_query
@beartype
async def get_tool_args_from_metadata(
    *,
    developer_id: UUID,
    agent_id: UUID,
    session_id: UUID | None = None,
    task_id: UUID | None = None,
    tool_type: Literal["integration", "api_call"] = "integration",
    arg_type: Literal["args", "setup", "headers"] = "args",
) -> tuple[str, list]:
    match session_id, task_id:
        case (None, task_id) if task_id is not None:
            return (
                tools_args_for_task_query,
                [
                    agent_id,
                    task_id,
                    f"x-{tool_type}-{arg_type}",
                    developer_id,
                ],
            )

        case (session_id, None) if session_id is not None:
            return (
                tool_args_for_session_query,
                [agent_id, session_id, f"x-{tool_type}-{arg_type}", developer_id],
            )

        case (_, _):
            raise ValueError("Either session_id or task_id must be provided")
