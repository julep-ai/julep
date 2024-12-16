import asyncpg
import json

from ..env import db_dsn
from ..web import app


async def get_pg_client():
    # TODO: Create a postgres connection pool
    client = getattr(app.state, "pg_client", await asyncpg.connect(db_dsn))
    if not hasattr(app.state, "pg_client"):
        await client.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )
        app.state.pg_client = client

    return client
