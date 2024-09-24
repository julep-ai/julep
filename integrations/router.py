from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .integrations import execute_integration

router = APIRouter()


class IntegrationRequest(BaseModel):
    integration_name: str
    parameters: dict


class IntegrationResponse(BaseModel):
    result: str


@router.post("/execute")
async def execute(request: IntegrationRequest) -> IntegrationResponse:
    try:
        result = await execute_integration(request.integration_name, request.parameters)
        return IntegrationResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
