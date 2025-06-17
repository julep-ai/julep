from typing import Any

from beartype import beartype
from httpx import AsyncClient

from ..env import integration_service_url

__all__: list[str] = ["get_available_integrations", "run_integration_service"]


@beartype
async def run_integration_service(
    *,
    provider: str,
    arguments: dict,
    setup: dict | None = None,
    method: str | None = None,
) -> Any:
    slug = f"{provider}/{method}" if method else provider
    url = f"{integration_service_url}/execute/{slug}"

    setup = setup or None

    async with AsyncClient(timeout=600) as client:
        response = await client.post(
            url,
            json={"arguments": arguments, "setup": setup},
        )
        response.raise_for_status()

        return response.json()


@beartype
async def get_available_integrations() -> list[dict]:
    """Return the list of available integration providers."""

    url = f"{integration_service_url}/integrations"
    async with AsyncClient(timeout=10) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
