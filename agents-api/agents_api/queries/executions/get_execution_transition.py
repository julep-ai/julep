from typing import Any, Literal, TypeVar
from uuid import UUID

from asyncpg.exceptions import NoDataFoundError
from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Transition
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

sql_query = """
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
        NoDataFoundError: partialclass(HTTPException, status_code=404),
    }
)
@wrap_in_class(Transition, one=True, transform=_transform)
@pg_query
@beartype
async def get_execution_transition(
    *,
    developer_id: UUID,  # TODO: what to do with this parameter?
    transition_id: UUID | None = None,
    task_token: str | None = None,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    # At least one of `transition_id` or `task_token` must be provided
    assert (
        transition_id or task_token
    ), "At least one of `transition_id` or `task_token` must be provided."

    return (
        sql_query,
        [
            transition_id,
            task_token,
        ],
        "fetchrow",
    )
