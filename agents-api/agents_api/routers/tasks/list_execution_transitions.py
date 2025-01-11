from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status

from ...autogen.openapi_model import (
    ListResponse,
    Transition,
)
from ...queries.executions.list_execution_transitions import (
    list_execution_transitions as list_execution_transitions_query,
)
from .router import router


@router.get("/executions/{execution_id}/transitions", tags=["executions"])
async def list_execution_transitions(
    execution_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Transition]:
    transitions = await list_execution_transitions_query(
        execution_id=execution_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
    )

    return ListResponse[Transition](items=transitions)


@router.get("/executions/{execution_id}/transitions/{transition_id}", tags=["tasks"])
async def get_execution_transition(
    execution_id: UUID,
    transition_id: UUID,
) -> Transition:
    try:
        transitions = await list_execution_transitions_query(
            execution_id=execution_id,
            transition_id=transition_id,
        )
        if not transitions:
            raise IndexError
        return transitions[0]
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transition not found",
        )
