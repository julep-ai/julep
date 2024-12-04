import asyncio
from datetime import timedelta

from temporalio import workflow, activity
from temporalio.exceptions import ApplicationError

from ...activities import task_steps
from ...autogen.openapi_model import (
    CreateTransitionRequest,
    Transition,
    TransitionTarget,
)
from ...common.protocol.tasks import PartialTransition, StepContext
from ...common.retry_policies import DEFAULT_RETRY_POLICY
from . import TaskExecutionWorkflow, LastErrorInput

with workflow.unsafe.imports_passed_through():
    from ...env import (
        debug,
        temporal_schedule_to_close_timeout,
        testing,
        temporal_heartbeat_timeout,
    )


async def transition(
    context: StepContext, state: PartialTransition | None = None, **kwargs
) -> Transition:
    if state is None:
        state = PartialTransition()

    match context.is_last_step, context.cursor:
        case (True, TransitionTarget(workflow="main")):
            state.type = "finish"
        case (True, _):
            state.type = "finish_branch"
        case _, _:
            state.type = "step"

    transition_request = CreateTransitionRequest(
        current=context.cursor,
        **{
            "next": None
            if context.is_last_step
            else TransitionTarget(
                workflow=context.cursor.workflow, step=context.cursor.step + 1
            ),
            "metadata": {"step_type": type(context.current_step).__name__},
            "output": state.output,
            **state.model_dump(exclude_unset=True, exclude={"output"}),
            **kwargs,  # Override with any additional kwargs
        },
    )

    try:
        last_error = kwargs.pop("last_error", None)
        activity_info = activity.info()
        wf_handle = workflow.get_external_workflow_handle(activity_info.workflow_id)
        # TODO: do a better error check
        if last_error:
            await wf_handle.signal(TaskExecutionWorkflow.set_last_error, LastErrorInput(last_error=None))
            await asyncio.sleep(30)

        return await workflow.execute_activity(
            task_steps.transition_step,
            args=[context, transition_request],
            schedule_to_close_timeout=timedelta(
                seconds=30 if debug or testing else temporal_schedule_to_close_timeout
            ),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )

    except Exception as e:
        workflow.logger.error(f"Error in transition: {str(e)}")
        await wf_handle.signal(TaskExecutionWorkflow.set_last_error, LastErrorInput(last_error=e))
        raise ApplicationError(f"Error in transition: {e}") from e
