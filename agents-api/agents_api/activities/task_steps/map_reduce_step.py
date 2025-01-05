import logging

from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import MapReduceStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .base_evaluate import base_evaluate


@activity.defn
@beartype
async def map_reduce_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, MapReduceStep)

        output = await base_evaluate(
            context.current_step.over, await context.prepare_for_step()
        )

        return StepOutcome(output=output)

    except BaseException as e:
        logging.error(f"Error in map_reduce_step: {e}")
        return StepOutcome(error=str(e))
