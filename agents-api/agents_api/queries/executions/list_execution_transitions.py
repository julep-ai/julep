from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Transition
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Query to list execution transitions
list_execution_transitions_query = """
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
        asyncpg.InvalidRowCountInLimitClauseError: partialclass(
            HTTPException, status_code=400, detail="Invalid limit clause"
        ),
        asyncpg.InvalidRowCountInResultOffsetClauseError: partialclass(
            HTTPException, status_code=400, detail="Invalid offset clause"
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
    """
    List execution transitions for a given execution.

    Parameters:
        execution_id (UUID): The ID of the execution.
        limit (int): The number of transitions to return.
        offset (int): The number of transitions to skip.
        sort_by (Literal["created_at", "updated_at"]): The field to sort by.
        direction (Literal["asc", "desc"]): The direction to sort by.

    Returns:
        tuple[str, list]: SQL query and parameters for listing execution transitions.
    """
    return (
        list_execution_transitions_query,
        [
            str(execution_id),
            limit,
            offset,
            sort_by,
            direction,
        ],
    )
