from typing import Any, Literal, TypeVar
from uuid import UUID

from asyncpg.exceptions import NoDataFoundError
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Execution
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)
from .constants import OUTPUT_UNNEST_KEY

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """
SELECT * FROM latest_executions
WHERE
    execution_id = $1
LIMIT 1;
"""


@rewrap_exceptions(
    {
        NoDataFoundError: partialclass(HTTPException, status_code=404),
    }
)
@wrap_in_class(
    Execution,
    one=True,
    transform=lambda d: {
        "id": d.pop("execution_id"),
        **d,
        "output": d["output"][OUTPUT_UNNEST_KEY]
        if isinstance(d["output"], dict) and OUTPUT_UNNEST_KEY in d["output"]
        else d["output"],
    },
)
@pg_query
@beartype
async def get_execution(
    *,
    execution_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    return (sql_query, [execution_id], "fetchrow")
