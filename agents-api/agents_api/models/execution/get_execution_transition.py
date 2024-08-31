from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Transition
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
        AssertionError: partialclass(HTTPException, status_code=500),
    }
)
@wrap_in_class(Transition, one=True)
@cozo_query
@beartype
def get_execution_transition(
    *,
    developer_id: UUID,
    transition_id: UUID | None = None,
    task_token: str | None = None,
) -> tuple[list[str], dict]:
    # At least one of `transition_id` or `task_token` must be provided
    assert (
        transition_id or task_token
    ), "At least one of `transition_id` or `task_token` must be provided."

    if transition_id:
        transition_id = str(transition_id)
        filter = "id = to_uuid($transition_id)"

    else:
        filter = "task_token = $task_token"

    get_query = """
        ?[id, type, current, next, output, metadata, updated_at, created_at] :=
            *transitions {
                transition_id: id,
                type,
                current: current_tuple,
                next: next_tuple,
                output,
                metadata,
                updated_at,
                created_at,
            },
            current = {"workflow": current_tuple->0, "step": current_tuple->1},
            next = if(
                is_null(next_tuple),
                null,
                {"workflow": next_tuple->0, "step": next_tuple->1},
            ),
    """

    get_query += filter

    queries = [
        verify_developer_id_query(developer_id),
        get_query,
    ]

    return (queries, {"task_token": task_token, "transition_id": transition_id})
