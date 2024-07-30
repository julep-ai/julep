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
) -> tuple[str, dict]:
    # At least one of `transition_id` or `task_token` must be provided
    assert (
        transition_id or task_token
    ), "At least one of `transition_id` or `task_token` must be provided."

    fields = [k for k in Transition.model_fields.keys() if k != "id"]
    fields_str = ", ".join(fields)

    if transition_id:
        transition_id = str(transition_id)
        filter = "id = to_uuid($transition_id)"

    else:
        filter = "task_token = $task_token"

    get_query = f"""
    ?[id, {fields_str}] :=
        *transitions {{
            transition_id: id,
            {fields_str}
        }},
    """

    get_query += filter

    queries = [
        verify_developer_id_query(developer_id),
        get_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"task_token": task_token, "transition_id": transition_id})
