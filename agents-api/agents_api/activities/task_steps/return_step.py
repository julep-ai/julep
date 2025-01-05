from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import ReturnStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .base_evaluate import base_evaluate


@activity.defn
@beartype
async def return_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, ReturnStep)

        exprs: dict[str, str] = context.current_step.return_
        output = await base_evaluate(exprs, await context.prepare_for_step())

        return StepOutcome(output=output)

    except BaseException as e:
        activity.logger.error(f"Error in log_step: {e}")
        return StepOutcome(error=str(e))
