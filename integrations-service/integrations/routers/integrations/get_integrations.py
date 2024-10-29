from typing import List

from ...models.base_models import BaseProvider
from ...providers import available_providers
from .router import router


@router.get("/integrations", tags=["integrations"])
async def get_integrations() -> List[dict]:
    integrations = [
        {
            "provider": p.provider,
            "setup": p.setup.model_json_schema() if p.setup else None,
            "methods": [
                {
                    "method": m.method,
                    "description": m.description,
                    "arguments": m.arguments.model_json_schema(),
                    "output": m.output.model_json_schema(),
                }
                for m in p.methods
            ],
            "info": {
                "url": p.info.url,
                "docs": p.info.docs,
                "icon": p.info.icon,
                "friendly_name": p.info.friendly_name,
            },
        }
        for p in available_providers.values()
    ]
    return integrations
