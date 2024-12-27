from typing import Any

from beartype import beartype
from temporalio import activity

from ...activities.utils import simple_eval_dict
from ...common.protocol.tasks import StepContext, StepOutcome


@activity.defn
@beartype
async def evaluate_step(
    context: StepContext,
    additional_values: dict[str, Any] = {},
    override_expr: dict[str, str] | None = None,
) -> StepOutcome:
    try:
        expr = (
            override_expr
            if override_expr is not None
            else context.current_step.evaluate
        )

        values = await context.prepare_for_step(include_remote=True) | additional_values

        output = simple_eval_dict(expr, values)
        result = StepOutcome(output=output)

        return result

    except BaseException as e:
        activity.logger.error(f"Error in evaluate_step: {e}")
        return StepOutcome(error=str(e) or repr(e))
