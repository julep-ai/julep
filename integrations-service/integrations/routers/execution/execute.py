from typing import Optional

from fastapi import Body, HTTPException, Path

from ...models.base_models import IdentifierName
from ...models.execution import ExecutionRequest, ExecutionResponse
from ...utils.execute_integration import execute_integration
from .router import router


@router.post("/execute/{provider}", tags=["execution"])
async def execute(
    provider: IdentifierName,
    data: ExecutionRequest,
) -> ExecutionResponse:
    try:
        return await execute_integration(
            provider=provider, arguments=data.arguments, setup=data.setup
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
