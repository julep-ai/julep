import logging

from beartype import beartype
from simpleeval import simple_eval
from temporalio import activity

from ...autogen.openapi_model import MapReduceStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing


@beartype
async def map_reduce_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, MapReduceStep)

        return StepOutcome(
            output=simple_eval(
                context.current_step.map.over, names=context.model_dump()
            )
        )
    except BaseException as e:
        logging.error(f"Error in map_reduce_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported if_else_step directly
# They do the same thing, so we dont need to mock the if_else_step function
mock_if_else_step = map_reduce_step

map_reduce_step = activity.defn(name="map_reduce_step")(
    map_reduce_step if not testing else mock_if_else_step
)
