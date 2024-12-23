from typing import Any, Literal, TypeVar
from uuid import UUID

import sqlvalidator
from beartype import beartype

from ...autogen.openapi_model import Tool
from ...exceptions import InvalidSQLQuery
from ..utils import (
    pg_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """
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

# if not sql_query.is_valid():
#     raise InvalidSQLQuery("list_tools")


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
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
) -> tuple[str, list] | tuple[str, list, str]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)

    return (
        sql_query,
        [
            developer_id,
            agent_id,
            limit,
            offset,
            sort_by,
            direction,
        ],
    )
