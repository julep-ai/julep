from temporalio import activity

from ...autogen.openapi_model import ReturnStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing
from .base_evaluate import base_evaluate


async def return_step(context: StepContext) -> StepOutcome:
    # NOTE: This activity is only for returning immediately, so we just evaluate the expression
    #       Hence, it's a local activity and SHOULD NOT fail
    try:
        assert isinstance(context.current_step, ReturnStep)

        exprs: dict[str, str] = context.current_step.return_
        output = await base_evaluate(exprs, context.model_dump())

        result = StepOutcome(output=output)
        return result

    except BaseException as e:
        activity.logger.error(f"Error in log_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported return_step directly
# They do the same thing, so we dont need to mock the return_step function
mock_return_step = return_step

return_step = activity.defn(name="return_step")(
    return_step if not testing else mock_return_step
)
