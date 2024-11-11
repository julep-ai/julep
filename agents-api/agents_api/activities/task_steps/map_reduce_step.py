import logging

from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import MapReduceStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...common.storage_handler import auto_blob_store
from ...env import testing
from .base_evaluate import base_evaluate


@auto_blob_store
@beartype
async def map_reduce_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, MapReduceStep)

        output = await base_evaluate(
            context.current_step.over, context.prepare_for_step()
        )

        return StepOutcome(output=output)

    except BaseException as e:
        logging.error(f"Error in map_reduce_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported if_else_step directly
# They do the same thing, so we dont need to mock the if_else_step function
mock_if_else_step = map_reduce_step

map_reduce_step = activity.defn(name="map_reduce_step")(
    map_reduce_step if not testing else mock_if_else_step
)
