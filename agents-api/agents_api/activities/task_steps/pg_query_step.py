from typing import Any

from beartype import beartype
from temporalio import activity

from ... import queries
from ...app import app
from ...env import pg_dsn


@activity.defn
@beartype
async def pg_query_step(
    query_name: str,
    values: dict[str, Any],
    dsn: str = pg_dsn,
) -> Any:
    (module_name, name) = query_name.split(".")

    module = getattr(queries, module_name)
    query = getattr(module, name)
    return await query(**values, connection_pool=app.state.postgres_pool)
