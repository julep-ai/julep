from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import ReturnStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...common.storage_handler import auto_blob_store
from ...env import testing
from .base_evaluate import base_evaluate


@auto_blob_store
@beartype
async def return_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, ReturnStep)

        exprs: dict[str, str] = context.current_step.return_
        output = await base_evaluate(exprs, context.prepare_for_step())

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
