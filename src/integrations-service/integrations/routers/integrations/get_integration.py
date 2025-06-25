from fastapi import HTTPException

from ... import providers as available_providers
from ...models.base_models import BaseProvider
from .router import router


@router.get("/integrations/{provider}", tags=["integration"])
async def get_integration(provider: str) -> dict:
    integration: BaseProvider | None = getattr(available_providers, provider, None)

    if integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

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
