from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import SwitchStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ..utils import get_evaluator


@activity.defn
@beartype
async def switch_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, SwitchStep)

        # Assume that none of the cases evaluate to truthy
        output: int = -1
        cases: list[str] = [c.case for c in context.current_step.switch]

        evaluator = get_evaluator(names=await context.prepare_for_step())

        for i, case in enumerate(cases):
            result = evaluator.eval(case)

            if result:
                output = i
                break

        return StepOutcome(output=output)

    except BaseException as e:
        activity.logger.error(f"Error in switch_step: {e}")
        return StepOutcome(error=str(e))
