from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import LogStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .base_evaluate import base_evaluate


@activity.defn
@beartype
async def log_step(context: StepContext) -> StepOutcome:
    # NOTE: This activity is only for logging, so we just evaluate the expression
    #       Hence, it's a local activity and SHOULD NOT fail
    try:
        assert isinstance(context.current_step, LogStep)

        expr = context.current_step.log
        output = await base_evaluate(expr, await context.prepare_for_step())

        return StepOutcome(output=output)

    except BaseException as e:
        activity.logger.error(f"Error in log_step: {e}")
        return StepOutcome(error=str(e))
