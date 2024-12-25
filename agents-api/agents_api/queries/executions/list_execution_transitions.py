from typing import Any, Literal, TypeVar
from uuid import UUID

from asyncpg.exceptions import (
    InvalidRowCountInLimitClauseError,
    InvalidRowCountInResultOffsetClauseError,
)
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Transition
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """
SELECT * FROM transitions
WHERE
    execution_id = $1
ORDER BY 
    CASE WHEN $4 = 'created_at' AND $5 = 'asc' THEN created_at END ASC NULLS LAST,
    CASE WHEN $4 = 'created_at' AND $5 = 'desc' THEN created_at END DESC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'asc' THEN updated_at END ASC NULLS LAST,
    CASE WHEN $4 = 'updated_at' AND $5 = 'desc' THEN updated_at END DESC NULLS LAST
LIMIT $2 OFFSET $3;
"""


def _transform(d):
    current_step = d.pop("current_step")
    next_step = d.pop("next_step", None)

    return {
        "current": {
            "workflow": current_step[0],
            "step": current_step[1],
        },
        "next": {"workflow": next_step[0], "step": next_step[1]}
        if next_step is not None
        else None,
        **d,
    }


@rewrap_exceptions(
    {
        InvalidRowCountInLimitClauseError: partialclass(HTTPException, status_code=400),
        InvalidRowCountInResultOffsetClauseError: partialclass(
            HTTPException, status_code=400
        ),
    }
)
@wrap_in_class(
    Transition,
    transform=_transform,
)
@pg_query
@beartype
async def list_execution_transitions(
    *,
    execution_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, list]:
    return (
        sql_query,
        [
            str(execution_id),
            limit,
            offset,
            sort_by,
            direction,
        ],
    )
