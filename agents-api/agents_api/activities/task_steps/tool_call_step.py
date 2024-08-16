from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import (
    ToolCallStep,
)
from ...common.protocol.tasks import (
    StepContext,
)



@activity.defn
@beartype
async def tool_call_step(context: StepContext) -> dict:
    raise NotImplementedError()
    # assert isinstance(context.definition, ToolCallStep)

    # context.definition.tool_id
    # context.definition.arguments
    # # get tool by id
    # # call tool

    # return {}