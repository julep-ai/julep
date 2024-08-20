import logging

from beartype import beartype
from simpleeval import simple_eval
from temporalio import activity

from ...autogen.openapi_model import ForeachStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing


@beartype
async def for_each_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, ForeachStep)

        return StepOutcome(
            output=simple_eval(
                context.current_step.foreach.in_, names=context.model_dump()
            )
        )
    except BaseException as e:
        logging.error(f"Error in for_each_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported if_else_step directly
# They do the same thing, so we dont need to mock the if_else_step function
mock_if_else_step = for_each_step

for_each_step = activity.defn(name="for_each_step")(
    for_each_step if not testing else mock_if_else_step
)
