from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import ForeachStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .base_evaluate import base_evaluate


@activity.defn
@beartype
async def for_each_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, ForeachStep)

        output = await base_evaluate(
            context.current_step.foreach.in_, await context.prepare_for_step()
        )
        return StepOutcome(output=output)

    except BaseException as e:
        activity.logger.error(f"Error in for_each_step: {e}")
        return StepOutcome(error=str(e))
