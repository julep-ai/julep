import json

import asyncpg

from ..env import db_dsn


async def _init_conn(conn):
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def create_db_pool(dsn: str | None = None):
    return await asyncpg.create_pool(
        dsn if dsn is not None else db_dsn, init=_init_conn
    )
