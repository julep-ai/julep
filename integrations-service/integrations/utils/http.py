from functools import lru_cache
from typing import Optional

import httpx


@lru_cache(maxsize=1)
def get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        http2=True,
    )


async def get_client() -> httpx.AsyncClient:
    return get_http_client()
