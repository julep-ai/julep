from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import WaitForInputStep
from ...common.protocol.tasks import StepContext, StepOutcome
from ...common.storage_handler import auto_blob_store
from ...env import testing
from .base_evaluate import base_evaluate


@auto_blob_store(deep=True)
@beartype
async def wait_for_input_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, WaitForInputStep)

        exprs = context.current_step.wait_for_input.info
        output = await base_evaluate(exprs, context.prepare_for_step())

        result = StepOutcome(output=output)
        return result

    except BaseException as e:
        activity.logger.error(f"Error in wait_for_input_step: {e}")
        return StepOutcome(error=str(e))


mock_wait_for_input_step = wait_for_input_step

wait_for_input_step = activity.defn(name="wait_for_input_step")(
    wait_for_input_step if not testing else mock_wait_for_input_step
)
