import json
import logging
import sys

import asyncpg
from dependency_injector import containers, providers

from .agents.container import AgentsQueriesContainer


async def _init_conn(conn):
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pg_pool(dsn: str, max_size: int):
    pool = await asyncpg.create_pool(dsn=dsn, init=_init_conn, max_size=max_size)
    yield pool
    pool.close()


class Queries(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["agents_api.routers.agents"])
    config = providers.Configuration(yaml_files=["config.yml"])

    logging = providers.Resource(
        logging.basicConfig,
        stream=sys.stdout,
        level=config.log.level,
        format=config.log.format,
    )

    db_pool = providers.Resource(
        init_pg_pool,
        dsn=config.db.dsn,
        max_size=config.db.client_pool_max_size,
    )
    agents: AgentsQueriesContainer = providers.Container(
        AgentsQueriesContainer,
        db_pool=db_pool,
        config=config.agents,
    )
