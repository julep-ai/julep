from typing import Any

from beartype import beartype
from temporalio import activity

from ...common.protocol.tasks import StepContext, StepOutcome
from .base_evaluate import base_evaluate

@activity.defn
@beartype
async def evaluate_step(
    context: StepContext,
    additional_values: dict[str, Any] = {},
    override_expr: dict[str, str] | None = None,
) -> StepOutcome:
    try:
        expr = override_expr if override_expr is not None else context.current_step.evaluate

        values = await context.prepare_for_step() | additional_values

        output = await base_evaluate(expr, values)
        return StepOutcome(output=output)

    except BaseException as e:
        activity.logger.error(f"Error in evaluate_step: {e}")
        return StepOutcome(error=str(e) or repr(e), output=None)
