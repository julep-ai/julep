from typing import Any, TypeVar
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

sql_query = sqlvalidator.parse("""
SELECT * FROM tools
WHERE
    developer_id = $1 AND
    agent_id = $2 AND
    tool_id = $3
LIMIT 1
""")

if not sql_query.is_valid():
    raise InvalidSQLQuery("get_tool")


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
        "id": UUID(d.pop("tool_id")),
        d["type"]: d.pop("spec"),
        **d,
    },
    one=True,
)
@pg_query
@beartype
def get_tool(
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
