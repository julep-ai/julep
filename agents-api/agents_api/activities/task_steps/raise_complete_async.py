import base64
from temporalio import activity

from ...autogen.openapi_model import CreateTransitionRequest
from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)
from .transition_step import original_transition_step


@activity.defn
async def raise_complete_async(context: StepContext, output: StepOutcome) -> None:
    # TODO: Create a transtition to "wait" and save the captured_token to the transition
    
    activity_info = activity.info()

    captured_token = activity_info.task_token
    activity_id = activity_info.activity_id
    workflow_run_id = activity_info.workflow_run_id
    workflow_id = activity_info.workflow_id
    print("activity_id")
    print(activity_id)
    captured_token = captured_token.decode("latin-1")
    transition_info = CreateTransitionRequest(
        current=context.cursor,
        type="wait",
        next=None,
        output=output,
        task_token=captured_token,
        metadata={
            "x-activity-id": activity_id,
            "workflow_run_id": workflow_run_id,
            "workflow_id": workflow_id,
        },
    )

    await original_transition_step(context, transition_info)

    # await transition(context, output=output, type="wait", next=None, task_token=captured_token)

    print("transition to wait called")
    activity.raise_complete_async()
