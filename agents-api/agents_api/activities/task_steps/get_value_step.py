from beartype import beartype
from temporalio import activity

from ...common.protocol.tasks import StepContext, StepOutcome
from ...common.storage_handler import auto_blob_store
from ...env import testing


# TODO: We should use this step to query the parent workflow and get the value from the workflow context
# SCRUM-1
@auto_blob_store(deep=True)
@beartype
async def get_value_step(
    context: StepContext,
) -> StepOutcome:
    key: str = context.current_step.get  # noqa: F841
    raise NotImplementedError("Not implemented yet")


# Note: This is here just for clarity. We could have just imported get_value_step directly
# They do the same thing, so we dont need to mock the get_value_step function
mock_get_value_step = get_value_step

get_value_step = activity.defn(name="get_value_step")(
    get_value_step if not testing else mock_get_value_step
)
