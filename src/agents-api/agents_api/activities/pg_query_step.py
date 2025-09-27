from typing import Any

from beartype import beartype
from temporalio import activity

from .. import queries
from ..env import testing


@beartype
async def pg_query_step(
    query_name: str,
    file_name: str,
    values: dict[str, Any],
) -> Any:
    (module_name, name) = file_name.split(".")

    module = getattr(queries, module_name)
    query_module = getattr(module, name)
    query = getattr(query_module, query_name)

    return await query(**values)


mock_pg_query_step = pg_query_step

pg_query_step = activity.defn(name="pg_query_step")(
    pg_query_step if not testing else mock_pg_query_step,
)
