from .router import router

from fastapi import APIRouter, HTTPException
from typing import Optional
from ...models.models import IntegrationDef
from ...utils.integrations import (
    dalle_image_generator,
    duckduckgo_search,
    hacker_news,
    twitter,
    weather,
    wikipedia,
)
from .get_integrations import get_integrations

router = APIRouter()

def convert_to_openai_tool(integration: IntegrationDef) -> dict:
    return {
        "type": "function",
        "function": {
            "name": integration.provider,
            "description": integration.description,
            "parameters": {
                "type": "object",
                "properties": integration.arguments,
                "required": [k for k, v in integration.arguments.items() if v.get("required", False)]
            }
        }
    }

@router.get("/integrations/{provider}/{method}/tool", tags=["integrations"])
async def get_integration_tool(provider: str, method: Optional[str] = None):
    integrations = await get_integrations()
    
    for integration in integrations:
        if integration.provider == provider and (method is None or integration.method == method):
            return convert_to_openai_tool(integration)
    
    raise HTTPException(status_code=404, detail="Integration not found")
