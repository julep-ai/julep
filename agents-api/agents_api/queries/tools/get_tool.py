from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Tool
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for getting a tool
tools_query = parse_one("""
SELECT * FROM tools
WHERE
    developer_id = $1 AND
    agent_id = $2 AND
    tool_id = $3
LIMIT 1
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="Developer or agent not found",
        ),
    }
)
@wrap_in_class(
    Tool,
    transform=lambda d: {
        "id": d.pop("tool_id"),
        d["type"]: d.pop("spec"),
        **d,
    },
    one=True,
)
@pg_query
@beartype
async def get_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
) -> tuple[str, list]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    return (
        tools_query,
        [
            developer_id,
            agent_id,
            tool_id,
        ],
    )
