from typing import Any
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for deleting a tool
tools_query = parse_one("""
DELETE FROM 
    tools 
WHERE
    developer_id = $1 AND
    agent_id = $2 AND
    tool_id = $3
RETURNING *
""").sql(pretty=True)


@rewrap_exceptions(
    {
        # Handle foreign key constraint
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="Developer or agent not found",
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {"id": d["tool_id"], "deleted_at": utcnow(), "jobs": [], **d},
)
@pg_query
@beartype
async def delete_tool(
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
