from typing import Optional

from fastapi import HTTPException

from ...models.base_models import BaseProvider, BaseProviderMethod
from .router import router


def convert_to_openai_tool(
    provider: BaseProvider, method: Optional[BaseProviderMethod] = None
) -> dict:
    method = method or provider.methods[0]
    name = f"{provider.provider}_{method.method}"
    description = method.description
    arguments = method.arguments.model_json_schema()

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": arguments,
        },
    }


@router.get("/integrations/{provider}/tool", tags=["integration_tool"])
@router.get("/integrations/{provider}/{method}/tool", tags=["integration_tool"])
async def get_integration_tool(provider: str, method: Optional[str] = None):
    from ...providers import available_providers

    provider_obj: BaseProvider | None = available_providers.get(provider, None)

    if not provider_obj:
        raise HTTPException(status_code=404, detail="Integration not found")

    if method:
        for m in provider_obj.methods:
            if m.method == method:
                return convert_to_openai_tool(provider_obj, m)
    else:
        return convert_to_openai_tool(provider_obj)

    raise HTTPException(status_code=404, detail="Integration not found")
