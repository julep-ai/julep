from xxhash import xxh64

from operator import itemgetter
from typing import Optional

from aiocache import cached, multi_cached, Cache
from aiocache.serializers import PickleSerializer

import httpx

embaas_batch_cache = multi_cached(
    keys_from_attr="texts",
    key_builder=lambda prompt, *_, **__: xxh64(prompt).hexdigest(),
    cache=Cache.REDIS,
    port=6379,
    namespace="embaas",
    serializer=PickleSerializer(),
    ttl=0.3 * (365 * 24 * 60 * 60),  # 0.3 years
    # aiocache_wait_for_write=False,
)

at = lambda ls, idx, default=None: ls[idx] if idx < len(ls) else default
key_builder_single = (
    lambda f, *args, **kwargs: kwargs.get("instruction", at(args, 1, "query"))
    + "_"
    + xxh64(kwargs.get("text", at(args, 0))).hexdigest()
)

embaas_cache = cached(
    key_builder=key_builder_single,
    cache=Cache.REDIS,
    port=6379,
    namespace="embaas_single",
    ttl=0.3 * (365 * 24 * 60 * 60),  # 0.3 years
    serializer=PickleSerializer(),
    # aiocache_wait_for_write=False,
)


# @embaas_batch_cache
async def embed(
    texts: list[str],
    model: str = "e5-large-v2",
    instruction: Optional[str] = None,
    endpoint: str = "https://api.embaas.io/v1/embeddings/",
    api_key: Optional[str] = None,
) -> dict[str, str]:
    if not api_key:
        import os

        api_env_key = "EMBAAS_API_KEY"
        api_key = os.getenv(api_env_key)

        assert api_key, f"API key must be passed or set in env as {api_env_key}"

    if model.startswith("e5"):
        allowed_e5_instructions = ["query", "passage"]

        assert (
            instruction in allowed_e5_instructions
        ), f"`instruction` required for e5 models, must be one of {', '.join(allowed_e5_instructions)}"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    data = dict(
        texts=texts,
        model=model,
    )

    if instruction:
        data["instruction"] = instruction

    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, headers=headers, json=data)

    response.raise_for_status()
    result = response.json()
    data = result.get("data")

    assert data, "No data returned"

    data = sorted(data, key=itemgetter("index"))
    return {text: item["embedding"] for text, item in zip(texts, data)}


# @embaas_cache
async def embed_one(text: str, instruction: str) -> list[float]:
    result = await embed([text], instruction=instruction)
    return result[text]
