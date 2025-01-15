from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import WaitForInputStep
from ...common.protocol.tasks import StepContext, StepOutcome
from .base_evaluate import base_evaluate


@activity.defn
@beartype
async def wait_for_input_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, WaitForInputStep)

        exprs = context.current_step.wait_for_input.info
        output = await base_evaluate(exprs, await context.prepare_for_step())

        return StepOutcome(output=output)

    except BaseException as e:
        activity.logger.error(f"Error in wait_for_input_step: {e}")
        return StepOutcome(error=str(e))
