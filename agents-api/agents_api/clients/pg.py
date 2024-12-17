import json
import asyncpg


async def _init_conn(conn):
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def create_db_pool(dsn: str):
    return await asyncpg.create_pool(dsn, init=_init_conn)
