from temporalio import activity

from ...common.protocol.tasks import (
    StepContext,
    StepOutcome,
)


@activity.defn
async def raise_complete_async(context: StepContext, output: StepOutcome) -> None:
    from ...workflows.task_execution.transition import transition
    # TODO: Create a transtition to "wait" and save the captured_token to the transition
    
    captured_token = activity.info().task_token
    captured_token = str(captured_token)
    print("calling transition to wait...")
    await transition(context, output=output, type="wait", next=None, task_token=captured_token)
    print("transition to wait called")
    activity.raise_complete_async()
