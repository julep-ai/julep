import httpx
from ..env import embedding_service_url, truncate_embed_text


async def embed(
    inputs: list[str],
    join_inputs=True,
) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            embedding_service_url,
            headers={
                "Content-Type": "application/json",
            },
            json={
                "inputs": "\n\n".join(inputs) if join_inputs else inputs,
                "normalize": True,
                "truncate": truncate_embed_text,
            },
        )
        resp.raise_for_status()

        return resp.json()
