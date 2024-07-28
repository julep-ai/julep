from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Transition
from ..utils import cozo_query, wrap_in_class


@wrap_in_class(Transition)
@cozo_query
@beartype
def list_execution_transitions(
    *,
    execution_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at", "deleted_at"] = "created_at",
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
