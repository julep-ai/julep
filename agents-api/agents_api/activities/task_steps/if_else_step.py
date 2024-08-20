from beartype import beartype
from simpleeval import simple_eval
from temporalio import activity

from ...autogen.openapi_model import IfElseWorkflowStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing


@beartype
async def if_else_step(context: StepContext) -> StepOutcome:
    # NOTE: This activity is only for logging, so we just evaluate the expression
    #       Hence, it's a local activity and SHOULD NOT fail
    try:
        assert isinstance(context.current_step, IfElseWorkflowStep)

        expr: str = context.current_step.if_
        output = simple_eval(expr, names=context.model_dump())
        output: bool = bool(output)

        result = StepOutcome(output=output)
        return result

    except BaseException as e:
        activity.logger.error(f"Error in if_else_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported if_else_step directly
# They do the same thing, so we dont need to mock the if_else_step function
mock_if_else_step = if_else_step

if_else_step = activity.defn(name="if_else_step")(
    if_else_step if not testing else mock_if_else_step
)
