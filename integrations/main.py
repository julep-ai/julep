from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from integrations import execute_integration

app = FastAPI()


class IntegrationRequest(BaseModel):
    integration_name: str
    parameters: dict


class IntegrationResponse(BaseModel):
    result: str


@app.post("/execute", response_model=IntegrationResponse)
async def execute(request: IntegrationRequest):
    try:
        result = await execute_integration(request.integration_name, request.parameters)
        return IntegrationResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
