from ...providers import providers
from .router import router


@router.get("/integrations/{provider}", tags=["integration"])
async def get_integration(provider: str) -> dict:
    integration = providers[provider]
    return {
        "provider": integration.provider,
        "setup": integration.setup.model_json_schema() if integration.setup else None,
        "methods": [
            {
                "method": m.method,
                "description": m.description,
                "arguments": m.arguments.model_json_schema(),
                "output": m.output.model_json_schema(),
            }
            for m in integration.methods
        ],
        "info": integration.info.model_dump_json(),
    }
