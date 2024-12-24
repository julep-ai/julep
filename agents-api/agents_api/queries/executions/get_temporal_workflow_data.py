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
SELECT id, run_id, result_run_id, first_execution_run_id FROM temporal_executions_lookup
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
async def get_temporal_workflow_data(
    *,
    execution_id: UUID,
) -> tuple[str, dict]:
    # Executions are allowed direct GET access if they have execution_id
    execution_id = str(execution_id)

    return (
        sql_query,
        [
            execution_id,
        ],
    )
