from temporalio import activity

from ...activities.task_steps.utils import simple_eval_dict
from ...autogen.openapi_model import ReturnStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing


async def return_step(
    context: StepContext,
) -> StepOutcome:
    assert isinstance(context.current_step, ReturnStep)

    exprs: dict[str, str] = context.current_step.return_
    output = simple_eval_dict(exprs, values=context.model_dump())

    result = StepOutcome(output=output)
    return result


# Note: This is here just for clarity. We could have just imported return_step directly
# They do the same thing, so we dont need to mock the return_step function
mock_return_step = return_step

return_step = activity.defn(name="return_step")(
    return_step if not testing else mock_return_step
)
