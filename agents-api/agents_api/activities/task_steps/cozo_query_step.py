from typing import Any

from beartype import beartype
from temporalio import activity

from ... import models
from ...env import testing


@beartype
async def cozo_query_step(
    query_name: str,
    values: dict[str, Any],
) -> Any:
    (module_name, name) = query_name.split(".")

    module = getattr(models, module_name)
    query = getattr(module, name)
    return query(**values)


# Note: This is here just for clarity. We could have just imported cozo_query_step directly
# They do the same thing, so we dont need to mock the cozo_query_step function
mock_cozo_query_step = cozo_query_step

cozo_query_step = activity.defn(name="cozo_query_step")(
    cozo_query_step if not testing else mock_cozo_query_step
)
