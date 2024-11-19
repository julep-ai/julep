from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import LogStep
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from ...common.storage_handler import auto_blob_store
from ...common.utils.template import render_template
from ...env import testing


@auto_blob_store(deep=True)
@beartype
async def log_step(context: StepContext) -> StepOutcome:
    # NOTE: This activity is only for logging, so we just evaluate the expression
    #       Hence, it's a local activity and SHOULD NOT fail
    try:
        assert isinstance(context.current_step, LogStep)

        template: str = context.current_step.log
        output = await render_template(
            template,
            context.prepare_for_step(include_remote=True),
            skip_vars=["developer_id"],
        )

        result = StepOutcome(output=output)
        return result

    except BaseException as e:
        activity.logger.error(f"Error in log_step: {e}")
        return StepOutcome(error=str(e))


# Note: This is here just for clarity. We could have just imported log_step directly
# They do the same thing, so we dont need to mock the log_step function
mock_log_step = log_step

log_step = activity.defn(name="log_step")(log_step if not testing else mock_log_step)
