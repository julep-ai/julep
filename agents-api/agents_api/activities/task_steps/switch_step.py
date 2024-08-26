from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import SwitchStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing
from ..utils import get_evaluator


@beartype
async def switch_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, SwitchStep)

        # Assume that none of the cases evaluate to truthy
        output: int = -1
        cases: list[str] = [c.case for c in context.current_step.switch]

        evaluator = get_evaluator(names=context.model_dump())

        for i, case in enumerate(cases):
            result = evaluator.eval(case)

            if result:
                output = i
                break

        result = StepOutcome(output=output)
        return result

    except BaseException as e:
        activity.logger.error(f"Error in switch_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported switch_step directly
# They do the same thing, so we dont need to mock the switch_step function
mock_switch_step = switch_step

switch_step = activity.defn(name="switch_step")(
    switch_step if not testing else mock_switch_step
)
