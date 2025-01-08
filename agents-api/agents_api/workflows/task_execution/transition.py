from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ...activities import task_steps
    from ...autogen.openapi_model import (
        CreateTransitionRequest,
        Transition,
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
) -> Transition:
    if state is None:
        state = PartialTransition()

    error_type = kwargs.get("type")

    if state.type is not None and state.type == "error":
        error_type = "error"
    elif state.type is not None and state.type == "cancelled":
        error_type = "cancelled"

    if error_type and error_type == "cancelled":
        state.type = "cancelled"
    elif error_type and error_type == "error":
        state.type = "error"
    else:
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
        workflow.logger.error(f"Error in transition: {e!s}")
        raise
