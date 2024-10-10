from uuid import UUID

from ...autogen.openapi_model import (
    Execution,
)
from ...models.execution.get_execution import (
    get_execution as get_execution_query,
)
from .router import router


@router.get("/executions/{execution_id}", tags=["executions"])
async def get_execution_details(execution_id: UUID) -> Execution:
    return get_execution_query(execution_id=execution_id)
