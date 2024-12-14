import asyncpg

from ..env import db_dsn
from ..web import app


async def get_pg_client():
    client = getattr(app.state, "pg_client", await asyncpg.connect(db_dsn))
    if not hasattr(app.state, "pg_client"):
        app.state.pg_client = client

    return client
