from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import SwitchStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...common.storage_handler import auto_blob_store
from ...env import testing
from ..utils import get_evaluator


@auto_blob_store
@beartype
async def switch_step(context: StepContext) -> StepOutcome:
    try:
        assert isinstance(context.current_step, SwitchStep)

        # Assume that none of the cases evaluate to truthy
        output: int = -1
        cases: list[str] = [c.case for c in context.current_step.switch]

        evaluator = get_evaluator(names=context.prepare_for_step())

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


mock_switch_step = switch_step

switch_step = activity.defn(name="switch_step")(
    switch_step if not testing else mock_switch_step
)
