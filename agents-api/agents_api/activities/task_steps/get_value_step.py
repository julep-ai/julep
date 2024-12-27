from beartype import beartype
from temporalio import activity

from ...common.protocol.tasks import StepContext, StepOutcome

# TODO: We should use this step to query the parent workflow and get the value from the workflow context
# SCRUM-1


@activity.defn
@beartype
async def get_value_step(
    context: StepContext,
) -> StepOutcome:
    key: str = context.current_step.get  # noqa: F841
    raise NotImplementedError("Not implemented yet")
