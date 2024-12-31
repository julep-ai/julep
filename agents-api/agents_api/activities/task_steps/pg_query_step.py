from typing import Any

from beartype import beartype
from temporalio import activity

from ... import queries
from ...app import lifespan
from ...env import pg_dsn
from ..container import container


@activity.defn
@lifespan(container)
@beartype
async def pg_query_step(
    query_name: str,
    values: dict[str, Any],
    dsn: str = pg_dsn,
) -> Any:
    (module_name, name) = query_name.split(".")

    module = getattr(queries, module_name)
    query = getattr(module, name)
    return await query(**values, connection_pool=container.state.postgres_pool)
