from typing import Any

from beartype import beartype
from temporalio import activity

from ...activities.task_steps.utils import simple_eval_dict
from ...autogen.openapi_model import EvaluateStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)


@activity.defn
@beartype
async def evaluate_step(
    context: StepContext[EvaluateStep],
) -> StepOutcome[dict[str, Any]]:
    exprs = context.definition.arguments
    output = simple_eval_dict(exprs, values=context.model_dump())

    return StepOutcome(output=output)
