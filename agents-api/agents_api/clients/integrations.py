from typing import Any

from beartype import beartype
from httpx import AsyncClient, Client

from ..env import integration_service_url

__all__: list[str] = ["run_integration_service"]


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
def convert_to_openai_tool(
    *,
    provider: str,
    method: str | None = None,
) -> Any:
    slug = f"{provider}/{method}" if method else provider
    url = f"{integration_service_url}/integrations/{slug}/tool"

    with Client(timeout=600) as client:
        response = client.get(
            url,
        )
        response.raise_for_status()

        return response.json()