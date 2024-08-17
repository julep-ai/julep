from beartype import beartype
from temporalio import activity

from ...autogen.openapi_model import (
    IfElseWorkflowStep,
)
from ...common.protocol.tasks import (
    StepContext,
)


@activity.defn
@beartype
async def if_else_step(context: StepContext[IfElseWorkflowStep]) -> dict:
    raise NotImplementedError()
    # context_data: dict = context.model_dump()

    # next_workflow = (
    #     context.current_step.then
    #     if simple_eval(context.current_step.if_, names=context_data)
    #     else context.current_step.else_
    # )

    # return {"goto_workflow": next_workflow}
