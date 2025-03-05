from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Tool
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for listing tools
tools_query = """
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
"""


@rewrap_exceptions(common_db_exceptions("tool", ["list"]))
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

    # Validate parameters
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if sort_by not in ["created_at", "updated_at"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be greater than 0")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

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
