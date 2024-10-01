from typing import Any, List

from beartype import beartype
from httpx import AsyncClient

from ..env import integration_service_url

__all__: List[str] = ["run_integration_service"]


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

    async with AsyncClient() as client:
        response = await client.post(
            url,
            json={"arguments": arguments, "setup": setup},
        )
        response.raise_for_status()

        return response.json()
