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
SELECT * FROM temporal_executions_lookup
WHERE
    execution_id = $1
LIMIT 1;
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
async def lookup_temporal_data(
    *,
    developer_id: UUID,  # TODO: what to do with this parameter?
    execution_id: UUID,
) -> tuple[str, list]:
    developer_id = str(developer_id)
    execution_id = str(execution_id)

    return (
        sql_query,
        execution_id,
    )
