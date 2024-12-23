from typing import Any, TypeVar
from uuid import UUID

import sqlvalidator
from beartype import beartype

from ...autogen.openapi_model import Execution
from ..utils import (
    pg_query,
    wrap_in_class,
)
from .constants import OUTPUT_UNNEST_KEY

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = sqlvalidator.parse("""
SELECT * FROM executions
WHERE
    execution_id = $1
LIMIT 1
""")


# @rewrap_exceptions(
#     {
#         AssertionError: partialclass(HTTPException, status_code=404),
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(
    Execution,
    one=True,
    transform=lambda d: {
        **d,
        "output": d["output"][OUTPUT_UNNEST_KEY]
        if isinstance(d["output"], dict) and OUTPUT_UNNEST_KEY in d["output"]
        else d["output"],
    },
)
@pg_query
@beartype
def get_execution(
    *,
    execution_id: UUID,
) -> tuple[str, dict]:
    return (
        sql_query.format(),
        [execution_id],
    )
