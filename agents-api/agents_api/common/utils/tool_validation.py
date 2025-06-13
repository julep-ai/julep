from __future__ import annotations

from async_lru import alru_cache
from fastapi import HTTPException
from httpx import HTTPError

from ...autogen.openapi_model import CreateToolRequest, UpdateToolRequest
from ...clients.integrations import get_available_integrations
from ..exceptions.tools import ToolValidationError


@alru_cache(ttl=60)
async def _get_providers() -> dict[str, dict]:
    providers = await get_available_integrations()
    return {p["provider"]: p for p in providers}


async def validate_tool(tool: CreateToolRequest | UpdateToolRequest) -> None:
    """Validate a tool definition against available providers."""

    if tool.type != "integration" or tool.integration is None:
        return

    try:
        providers = await _get_providers()
    except HTTPError as e:
        raise HTTPException(status_code=502, detail=str(e))

    provider = tool.integration.provider
    provider_info = providers.get(provider)
    if provider_info is None:
        msg = f"Unknown provider: {provider}"
        raise ToolValidationError(msg)

    method = tool.integration.method or provider_info["methods"][0]["method"]
    valid_methods = {m["method"] for m in provider_info["methods"]}
    if method not in valid_methods:
        msg = f"Unknown method '{method}' for provider '{provider}'"
        raise ToolValidationError(msg)
