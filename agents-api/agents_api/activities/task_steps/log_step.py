import logging

from simpleeval import simple_eval
from temporalio import activity

from ...autogen.openapi_model import LogStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing


async def log_step(
    context: StepContext,
) -> StepOutcome:
    # NOTE: This activity is only for logging, so we just evaluate the expression
    #       Hence, it's a local activity and SHOULD NOT fail
    try:
        assert isinstance(context.current_step, LogStep)

        expr: str = context.current_step.log
        output = simple_eval(expr, names=context.model_dump())

        result = StepOutcome(output=output)
        return result

    except Exception as e:
        logging.error(f"Error in log_step: {e}")
        return StepOutcome(output=None)


# Note: This is here just for clarity. We could have just imported log_step directly
# They do the same thing, so we dont need to mock the log_step function
mock_log_step = log_step

log_step = activity.defn(name="log_step")(log_step if not testing else mock_log_step)
