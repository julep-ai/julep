from fastapi import HTTPException, status
from pydantic import UUID4

from agents_api.autogen.openapi_model import (
    Execution,
)
from agents_api.models.execution.get_execution import (
    get_execution as get_execution_query,
)

from .router import router


@router.get("/executions/{execution_id}", tags=["executions"])
async def get_execution_details(execution_id: UUID4) -> Execution:
    try:
        return get_execution_query(execution_id=execution_id)
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found"
        )
