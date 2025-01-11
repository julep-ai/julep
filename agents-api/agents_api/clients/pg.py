import json

import asyncpg

from ..env import pg_dsn


async def _init_conn(conn):
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def create_db_pool(dsn: str | None = None, **kwargs):
    return await asyncpg.create_pool(
        dsn if dsn is not None else pg_dsn, init=_init_conn, **kwargs
    )
