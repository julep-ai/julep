from fastapi import Body, HTTPException, Path

from ...models import IntegrationExecutionRequest, IntegrationExecutionResponse
from ...utils.execute_integration import execute_integration
from .router import router


@router.post("/execute/{provider}", tags=["execution"])
async def execute(
    provider: str = Path(..., description="The integration provider"),
    request: IntegrationExecutionRequest = Body(
        ..., description="The integration execution request"
    ),
) -> IntegrationExecutionResponse:
    try:
        result = await execute_integration(provider, request.setup, request.arguments)
        return IntegrationExecutionResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
