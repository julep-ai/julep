from typing import Any

from beartype import beartype
from temporalio import activity

from ...common.protocol.tasks import StepContext
from ...common.utils.expressions import evaluate_expressions


@activity.defn
@beartype
async def base_evaluate(
    exprs: Any,
    context: StepContext | None = None,
    values: dict[str, Any] | None = None,
    extra_lambda_strs: dict[str, str] | None = None,
) -> Any | list[Any] | dict[str, Any]:
    if context is None and values is None:
        msg = "Either context or values must be provided"
        raise ValueError(msg)

    values = values or {}
    if context:
        # NOTE: We limit the number of inputs to 50 to avoid excessive memory usage
        values.update(await context.prepare_for_step(limit=50))

    return evaluate_expressions(exprs, values=values, extra_lambda_strs=extra_lambda_strs)
