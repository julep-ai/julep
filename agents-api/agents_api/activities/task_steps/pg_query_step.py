from typing import Any

from async_lru import alru_cache
from beartype import beartype
from temporalio import activity

from ... import queries
from ...env import testing, db_dsn 

from ...clients.pg import create_db_pool

@alru_cache(maxsize=1)
async def get_db_pool(dsn: str):
    return await create_db_pool(dsn=dsn)

@beartype
async def pg_query_step(
    query_name: str,
    values: dict[str, Any],
    dsn: str = db_dsn,
) -> Any:
    pool = await get_db_pool(dsn=dsn)

    (module_name, name) = query_name.split(".")

    module = getattr(queries, module_name)
    query = getattr(module, name)
    return await query(**values, connection_pool=pool)


# Note: This is here just for clarity. We could have just imported pg_query_step directly
# They do the same thing, so we dont need to mock the pg_query_step function
mock_pg_query_step = pg_query_step

pg_query_step = activity.defn(name="pg_query_step")(
    pg_query_step if not testing else mock_pg_query_step
)
