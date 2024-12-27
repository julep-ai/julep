from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import IfElseWorkflowStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .base_evaluate import base_evaluate


@activity.defn
@beartype
async def if_else_step(context: StepContext) -> StepOutcome:
    # NOTE: This activity is only for logging, so we just evaluate the expression
    #       Hence, it's a local activity and SHOULD NOT fail
    try:
        assert isinstance(context.current_step, IfElseWorkflowStep)

        expr: str = context.current_step.if_
        output = await base_evaluate(expr, await context.prepare_for_step())
        output: bool = bool(output)

        result = StepOutcome(output=output)
        return result

    except BaseException as e:
        activity.logger.error(f"Error in if_else_step: {e}")
        return StepOutcome(error=str(e))
