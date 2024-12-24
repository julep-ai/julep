from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Execution
from ..utils import (
    pg_query,
    wrap_in_class,
)
from .constants import OUTPUT_UNNEST_KEY

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """
SELECT * FROM executions
WHERE
    developer_id = $1
    task_id = $2
ORDER BY 
    CASE WHEN $3 = 'created_at' AND $4 = 'asc' THEN created_at END ASC NULLS LAST,
    CASE WHEN $3 = 'created_at' AND $4 = 'desc' THEN created_at END DESC NULLS LAST,
    CASE WHEN $3 = 'updated_at' AND $4 = 'asc' THEN updated_at END ASC NULLS LAST,
    CASE WHEN $3 = 'updated_at' AND $4 = 'desc' THEN updated_at END DESC NULLS LAST
LIMIT $5 OFFSET $6;
"""


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(
    Execution,
    transform=lambda d: {
        **d,
        "output": d["output"][OUTPUT_UNNEST_KEY]
        if isinstance(d.get("output"), dict) and OUTPUT_UNNEST_KEY in d["output"]
        else d.get("output"),
    },
)
@pg_query
@beartype
async def list_executions(
    *,
    developer_id: UUID,
    task_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, list]:
    return (
        sql_query,
        [
            developer_id,
            task_id,
            sort_by,
            direction,
            limit,
            offset,
        ],
    )
