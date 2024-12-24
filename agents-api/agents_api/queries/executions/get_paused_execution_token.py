from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype

from ..utils import (
    pg_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """
SELECT * FROM transitions
WHERE
    execution_id = $1
    AND type = 'wait'
ORDER BY created_at DESC
LIMIT 1;
"""


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#         AssertionError: partialclass(HTTPException, status_code=500),
#     }
# )
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def get_paused_execution_token(
    *,
    developer_id: UUID,
    execution_id: UUID,
) -> tuple[str, list]:
    execution_id = str(execution_id)

    # TODO: what to do with this query?
    # check_status_query = """
    # ?[execution_id, status] :=
    #     *executions:execution_id_status_idx {
    #         execution_id,
    #         status,
    #     },
    #     execution_id = to_uuid($execution_id),
    #     status = "awaiting_input"

    # :limit 1
    # :assert some
    # """

    return (
        sql_query,
        [execution_id],
    )
