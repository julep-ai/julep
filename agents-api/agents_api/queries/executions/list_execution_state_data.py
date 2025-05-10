from datetime import timedelta
from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Transition
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions, partialclass
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to list execution transitions
list_execution_state_query = """
SELECT * FROM transitions
WHERE
    execution_id = $1
    AND (current_step).scope_id = $7
    AND metadata->>'step_type' = 'SetStep'
    AND created_at >= $6
    AND created_at >= (select created_at from executions where execution_id = $1 LIMIT 1)
ORDER BY
    CASE WHEN $4 = 'created_at' AND $5 = 'asc' THEN created_at END ASC NULLS LAST,
    CASE WHEN $4 = 'created_at' AND $5 = 'desc' THEN created_at END DESC NULLS LAST
LIMIT $2 OFFSET $3;
"""

# next is not null
# current.scope = next.scope
# (current_step).workflow NOT SIMILAR TO '%\\[[0-9]+\\]%'


def _transform(d):
    current_step = d.pop("current_step")
    next_step = d.pop("next_step", None)

    return {
        "id": d["transition_id"],
        "updated_at": utcnow(),
        "current": {
            "workflow": current_step[0],
            "step": current_step[1],
            "scope_id": current_step[2],
        },
        "next": {
            "workflow": next_step[0],
            "step": next_step[1],
            "scope_id": next_step[2],
        }
        if next_step is not None
        else None,
        "step_label": d["step_label"],
        **d,
    }


@rewrap_exceptions({
    asyncpg.InvalidRowCountInLimitClauseError: partialclass(
        HTTPException,
        status_code=400,
        detail="Invalid limit clause",
    ),
    asyncpg.InvalidRowCountInResultOffsetClauseError: partialclass(
        HTTPException,
        status_code=400,
        detail="Invalid offset clause",
    ),
    **common_db_exceptions("transition", ["list"]),
})
@wrap_in_class(
    Transition,
    transform=_transform,
)
@pg_query
@beartype
async def list_execution_state_data(
    *,
    execution_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    scope_id: UUID,
    search_window: timedelta = timedelta(weeks=2),
) -> tuple[str, list]:
    """
    List execution transitions for a given execution.

    Parameters:
        execution_id (UUID): The ID of the execution.
        limit (int): The number of transitions to return.
        offset (int): The number of transitions to skip.
        sort_by (Literal["created_at"]): The field to sort by.
        direction (Literal["asc", "desc"]): The direction to sort by.
        scope_id (UUID | None): Filter transitions by scope_id in current_step.

    Returns:
        tuple[str, list]: SQL query and parameters for listing execution transitions.
    """

    params = [
        str(execution_id),
        limit,
        offset,
        sort_by,
        direction,
        utcnow() - search_window,
        str(scope_id),
    ]

    return (list_execution_state_query, params)
