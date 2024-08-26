from beartype import beartype
from temporalio import activity

from ...common.protocol.tasks import (
    StepContext,
)


@activity.defn
@beartype
async def tool_call_step(context: StepContext) -> dict:
    raise NotImplementedError()
    # assert isinstance(context.current_step, ToolCallStep)

    # context.current_step.tool_id
    # context.current_step.arguments
    # # get tool by id
    # # call tool

    # return {}
