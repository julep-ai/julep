from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Transition
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# FIXME: Use latest_transitions instead of transitions
# Query to get an execution transition
get_execution_transition_query = """
SELECT * FROM transitions
WHERE
    transition_id = $1
    OR task_token = $2
LIMIT 1;
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
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="No executions found for the specified task",
        ),
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or task does not exist",
        ),
    }
)
@wrap_in_class(Transition, one=True, transform=_transform)
@pg_query
@beartype
async def get_execution_transition(
    *,
    transition_id: UUID | None = None,
    task_token: str | None = None,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Get an execution transition by its ID or task token.

    Parameters:
        transition_id (UUID | None): The ID of the transition.
        task_token (str | None): The task token.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for getting the execution transition.
    """
    # At least one of `transition_id` or `task_token` must be provided
    assert (
        transition_id or task_token
    ), "At least one of `transition_id` or `task_token` must be provided."

    return (
        get_execution_transition_query,
        [
            transition_id,
            task_token,
        ],
        "fetchrow",
    )
