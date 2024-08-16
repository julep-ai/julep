from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Transition
from ..utils import cozo_query, partialclass, rewrap_exceptions, wrap_in_class


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(Transition)
@cozo_query
@beartype
def list_execution_transitions(
    *,
    execution_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, dict]:
    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    query = f"""
        ?[id, execution_id, type, current, next, output, metadata, updated_at, created_at] :=
            *transitions {{
                execution_id,
                transition_id: id,
                type,
                current: current_tuple,
                next: next_tuple,
                output,
                metadata,
                updated_at,
                created_at,
            }},
            current = {{"state": current_tuple->0, "step": current_tuple->1}},
            next = if(
                isnull(next_tuple),
                null,
                {{"state": next_tuple->0, "step": next_tuple->1}},
            ),
            execution_id = to_uuid($execution_id)

        :limit $limit
        :offset $offset
        :sort {sort}
    """

    return (
        query,
        {
            "execution_id": str(execution_id),
            "limit": limit,
            "offset": offset,
        },
    )
