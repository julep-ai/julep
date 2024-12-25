from typing import Any, Literal, TypeVar
from uuid import UUID

from asyncpg.exceptions import NoDataFoundError
from beartype import beartype
from fastapi import HTTPException

from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
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


@rewrap_exceptions(
    {
        NoDataFoundError: partialclass(HTTPException, status_code=404),
    }
)
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def get_temporal_workflow_data(
    *,
    execution_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    # Executions are allowed direct GET access if they have execution_id
    execution_id = str(execution_id)

    return (
        sql_query,
        [
            execution_id,
        ],
        "fetchrow",
    )
