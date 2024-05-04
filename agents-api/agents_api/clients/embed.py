import httpx
from ..env import embedding_service_url, truncate_embed_text, embedding_model_id


async def embed(
    inputs: list[str],
    join_inputs=False,
    embedding_service_url: str = embedding_service_url,
    embedding_model_name: str = embedding_model_id,
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
                # FIXME: We should control the truncation ourselves and truncate before sending
                "truncate": truncate_embed_text,
                "model_id": embedding_model_name,
            },
        )
        resp.raise_for_status()

        return resp.json()
