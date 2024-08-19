from temporalio import activity

from ...activities.task_steps.utils import simple_eval_dict
from ...autogen.openapi_model import WaitForInputStep
from ...common.protocol.tasks import StepContext, StepOutcome
from ...env import testing


async def wait_for_input_step(context: StepContext) -> StepOutcome:
    assert isinstance(context.current_step, WaitForInputStep)

    exprs = context.current_step.wait_for_input
    output = simple_eval_dict(exprs, values=context.model_dump())

    result = StepOutcome(output=output)
    return result


# Note: This is here just for clarity. We could have just imported wait_for_input_step directly
# They do the same thing, so we dont need to mock the wait_for_input_step function
mock_wait_for_input_step = wait_for_input_step

wait_for_input_step = activity.defn(name="wait_for_input_step")(
    wait_for_input_step if not testing else mock_wait_for_input_step
)
