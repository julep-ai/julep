import logging
from temporalio import activity

from ...activities.task_steps.utils import simple_eval_dict
from ...autogen.openapi_model import EvaluateStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...env import testing


async def evaluate_step(
    context: StepContext[EvaluateStep],
) -> StepOutcome:
    # NOTE: This activity is only for returning immediately, so we just evaluate the expression
    #       Hence, it's a local activity and SHOULD NOT fail
    try:
        assert isinstance(context.current_step, EvaluateStep)

        exprs = context.current_step.evaluate
        output = simple_eval_dict(exprs, values=context.model_dump())

        result = StepOutcome(output=output)
        return result

    except Exception as e:
        logging.error(f"Error in log_step: {e}")
        return StepOutcome(output=None)


# Note: This is here just for clarity. We could have just imported evaluate_step directly
# They do the same thing, so we dont need to mock the evaluate_step function
mock_evaluate_step = evaluate_step

evaluate_step = activity.defn(name="evaluate_step")(
    evaluate_step if not testing else mock_evaluate_step
)
