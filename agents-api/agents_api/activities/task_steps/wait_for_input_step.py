from temporalio import activity

from ...autogen.openapi_model import WaitForInputStep
from ...common.protocol.tasks import StepContext, StepOutcome
from ...env import testing
from .base_evaluate import base_evaluate


async def wait_for_input_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, WaitForInputStep)

        exprs = context.current_step.wait_for_input
        output = await base_evaluate(exprs, context.model_dump())

        result = StepOutcome(output=output)
        return result

    except BaseException as e:
        activity.logger.error(f"Error in wait_for_input_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported wait_for_input_step directly
# They do the same thing, so we dont need to mock the wait_for_input_step function
mock_wait_for_input_step = wait_for_input_step

wait_for_input_step = activity.defn(name="wait_for_input_step")(
    wait_for_input_step if not testing else mock_wait_for_input_step
)
