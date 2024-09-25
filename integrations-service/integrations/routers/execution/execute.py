from fastapi import HTTPException

from ...models import IntegrationExecutionRequest, IntegrationExecutionResponse
from ...utils.execute_integration import execute_integration
from .router import router


@router.post("/execution", tags=["execution"])
async def execute(request: IntegrationExecutionRequest) -> IntegrationExecutionResponse:
    try:
        result = await execute_integration(request.integration_name, request.parameters)
        return IntegrationExecutionResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
