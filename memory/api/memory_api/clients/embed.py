import httpx
from ..env import embedding_service_url


async def embed(
    inputs: list[str],
) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            embedding_service_url,
            headers={
                "Content-Type": "application/json",
            },
            json={
                "inputs": "\n\n".join(inputs),
                "normalize": True,
                "truncate": False,
            },
        )
        resp.raise_for_status()

        return resp.json()
