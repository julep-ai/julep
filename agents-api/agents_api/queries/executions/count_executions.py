from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype

from ..utils import (
    pg_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """SELECT COUNT(*) FROM latest_executions
WHERE
    developer_id = $1
    AND task_id = $2;
"""


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def count_executions(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    return (sql_query, [developer_id, task_id], "fetchrow")
