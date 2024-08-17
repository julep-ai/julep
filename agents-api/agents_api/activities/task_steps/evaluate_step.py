from typing import Any

from beartype import beartype
from temporalio import activity

from ...activities.task_steps.utils import simple_eval_dict
from ...autogen.openapi_model import EvaluateStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing


@beartype
async def evaluate_step(
    context: StepContext[EvaluateStep],
) -> StepOutcome[dict[str, Any]]:
    exprs = context.definition.arguments
    output = simple_eval_dict(exprs, values=context.model_dump())

    return StepOutcome(output=output)


# Note: This is here just for clarity. We could have just imported evaluate_step directly
# They do the same thing, so we dont need to mock the evaluate_step function
mock_evaluate_step = evaluate_step

evaluate_step = activity.defn(name="evaluate_step")(
    evaluate_step if not testing else mock_evaluate_step
)
