from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Tool
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for listing tools
tools_query = parse_one("""
SELECT * FROM tools
WHERE
    developer_id = $1 AND
    agent_id = $2
ORDER BY 
    CASE WHEN $5 = 'created_at' AND $6 = 'desc' THEN tools.created_at END DESC NULLS LAST,
    CASE WHEN $5 = 'created_at' AND $6 = 'asc' THEN tools.created_at END ASC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'desc' THEN tools.updated_at END DESC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'asc' THEN tools.updated_at END ASC NULLS LAST
LIMIT $3 OFFSET $4;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=400,
            detail="Developer or agent not found",
        ),
    }
)
@wrap_in_class(
    Tool,
    transform=lambda d: {
        d["type"]: {
            **d.pop("spec"),
            "name": d["name"],
            "description": d["description"],
        },
        "id": d.pop("tool_id"),
        **d,
    },
)
@pg_query
@beartype
async def list_tools(
    *,
    developer_id: UUID,
    agent_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, list]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)

    return (
        tools_query,
        [
            developer_id,
            agent_id,
            limit,
            offset,
            sort_by,
            direction,
        ],
    )
