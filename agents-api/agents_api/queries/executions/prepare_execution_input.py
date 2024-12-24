from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype

from ...common.protocol.tasks import ExecutionInput
from ..utils import (
    pg_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """SELECT * FROM 
(
    SELECT to_jsonb(a) AS agents FROM (
        SELECT * FROM agents
        WHERE
            developer_id = $1  AND
            agent_id = $4
        LIMIT 1
    ) a
) AS agents,
(
    SELECT jsonb_agg(r) AS tools FROM (
        SELECT * FROM tools
        WHERE
            developer_id = $1 AND 
            task_id = $2
    ) r
) AS tools,
(
    SELECT to_jsonb(t) AS tasks FROM (
        SELECT * FROM tasks
        WHERE
            developer_id = $1 AND 
            task_id = $2
        LIMIT 1
    ) t
) AS tasks,
(
    SELECT to_jsonb(e) AS executions FROM (
        SELECT * FROM executions
        WHERE
            developer_id = $1 AND 
            task_id = $2 AND
            execution_id = $3
        LIMIT 1
    ) e
) AS executions;
"""


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#         AssertionError: lambda e: HTTPException(
#             status_code=429,
#             detail=str(e),
#             headers={"x-should-retry": "true"},
#         ),
#     }
# )
@wrap_in_class(
    ExecutionInput,
    one=True,
    transform=lambda d: {
        **d,
        "task": {
            "tools": [*d["task"].pop("tools")],
            **d["task"],
        },
        "agent_tools": [
            {tool["type"]: tool.pop("spec"), **tool} for tool in d["tools"]
        ],
    },
)
@pg_query
@beartype
async def prepare_execution_input(
    *,
    developer_id: UUID,
    task_id: UUID,
    execution_id: UUID,
) -> tuple[list[str], dict]:
    dummy_agent_id = UUID(int=0)

    return (
        sql_query,
        [
            str(developer_id),
            str(task_id),
            str(execution_id),
            str(dummy_agent_id),
        ],
    )
