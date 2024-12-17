import json
from contextlib import asynccontextmanager

import asyncpg

from ..env import db_dsn
from ..web import app


async def get_pg_pool(dsn: str = db_dsn, **kwargs):
    pool = getattr(app.state, "pg_pool", None)

    if pool is None:
        pool = await asyncpg.create_pool(dsn, **kwargs)
        app.state.pg_pool = pool

    return pool


@asynccontextmanager
async def get_pg_client(pool: asyncpg.Pool):
    async with pool.acquire() as client:
        await client.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )
        yield client
