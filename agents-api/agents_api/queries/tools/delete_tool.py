from typing import Any, TypeVar
from uuid import UUID

import sqlvalidator
from beartype import beartype

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...exceptions import InvalidSQLQuery
from ..utils import (
    pg_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


sql_query = sqlvalidator.parse("""
DELETE FROM 
    tools 
WHERE
    developer_id = $1 AND
    agent_id = $2 AND
    tool_id = $3
RETURNING *
""")

if not sql_query.is_valid():
    raise InvalidSQLQuery("delete_tool")


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {"id": d["tool_id"], "deleted_at": utcnow(), "jobs": [], **d},
    _kind="deleted",
)
@pg_query
@beartype
async def delete_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
) -> tuple[list[str], list]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    return (
        sql_query.format(),
        [
            developer_id,
            agent_id,
            tool_id,
        ],
    )
