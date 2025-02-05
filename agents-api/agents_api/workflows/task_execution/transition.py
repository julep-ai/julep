from datetime import timedelta

from temporalio import workflow
from temporalio.exceptions import ApplicationError, ActivityError

with workflow.unsafe.imports_passed_through():
    from ...activities import task_steps
    from ...autogen.openapi_model import (
        CreateTransitionRequest,
        TransitionTarget,
    )
    from ...common.protocol.tasks import PartialTransition, StepContext
    from ...common.retry_policies import DEFAULT_RETRY_POLICY
    from ...env import (
        debug,
        temporal_heartbeat_timeout,
        temporal_schedule_to_close_timeout,
        testing,
    )


async def transition(
    context: StepContext, state: PartialTransition | None = None, **kwargs
) -> CreateTransitionRequest:
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
        await workflow.execute_activity(
            task_steps.transition_step,
            args=[context, transition_request],
            schedule_to_close_timeout=timedelta(
                seconds=30 if debug or testing else temporal_schedule_to_close_timeout
            ),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )
        return transition_request

    except Exception as e:
        while isinstance(e, ActivityError) and getattr(e, "__cause__", None):
            e = e.__cause__
        workflow.logger.error(f"Error in transition: {e!s}")
        msg = f"Error in transition: {e}"
        raise ApplicationError(msg) from e
