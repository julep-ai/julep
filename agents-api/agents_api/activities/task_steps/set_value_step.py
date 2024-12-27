from typing import Any

from beartype import beartype
from temporalio import activity

from ...activities.utils import simple_eval_dict
from ...common.protocol.tasks import StepContext, StepOutcome

# TODO: We should use this step to signal to the parent workflow and set the value on the workflow context
# SCRUM-2


@activity.defn
@beartype
async def set_value_step(
    context: StepContext,
    additional_values: dict[str, Any] = {},
    override_expr: dict[str, str] | None = None,
) -> StepOutcome:
    try:
        expr = override_expr if override_expr is not None else context.current_step.set

        values = await context.prepare_for_step() | additional_values
        output = simple_eval_dict(expr, values)
        return StepOutcome(output=output)

    except BaseException as e:
        activity.logger.error(f"Error in set_value_step: {e}")
        return StepOutcome(error=str(e) or repr(e))
