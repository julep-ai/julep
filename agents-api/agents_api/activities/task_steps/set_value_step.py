from typing import Any

from beartype import beartype
from temporalio import activity

from ...activities.utils import simple_eval_dict
from ...common.protocol.tasks import StepContext, StepOutcome
from ...common.storage_handler import auto_blob_store
from ...env import testing


# TODO: We should use this step to signal to the parent workflow and set the value on the workflow context
# SCRUM-2
@auto_blob_store
@beartype
async def set_value_step(
    context: StepContext,
    additional_values: dict[str, Any] = {},
    override_expr: dict[str, str] | None = None,
) -> StepOutcome:
    try:
        expr = override_expr if override_expr is not None else context.current_step.set

        values = context.prepare_for_step() | additional_values
        output = simple_eval_dict(expr, values)
        result = StepOutcome(output=output)

        return result

    except BaseException as e:
        activity.logger.error(f"Error in set_value_step: {e}")
        return StepOutcome(error=str(e) or repr(e))


# Note: This is here just for clarity. We could have just imported set_value_step directly
# They do the same thing, so we dont need to mock the set_value_step function
mock_set_value_step = set_value_step

set_value_step = activity.defn(name="set_value_step")(
    set_value_step if not testing else mock_set_value_step
)
