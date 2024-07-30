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
        ?[id, execution_id, type, current, next, output, metadata, updated_at, created_at] := *transitions {{
            execution_id,
            transition_id: id,
            type,
            current,
            next,
            output,
            metadata,
            updated_at,
            created_at,
        }}, execution_id = to_uuid($execution_id)

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
