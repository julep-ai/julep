import asyncio
from typing import cast

from beartype import beartype
from fastapi import HTTPException
from temporalio import activity

from ...autogen.openapi_model import CreateTransitionRequest, Transition
from ...clients.temporal import get_workflow_handle
from ...common.protocol.tasks import ExecutionInput, StepContext
from ...common.storage_handler import load_from_blob_store_if_remote
from ...env import (
    temporal_activity_after_retry_timeout,
    testing,
    transition_requests_per_minute,
)
from ...exceptions import LastErrorInput, TooManyRequestsError
from ...models.execution.create_execution_transition import (
    create_execution_transition_async,
)
from ..utils import RateLimiter

# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=transition_requests_per_minute)


@beartype
async def transition_step(
    context: StepContext,
    transition_info: CreateTransitionRequest,
    last_error: BaseException | None = None,
) -> Transition:
    # Check rate limit first
    if not await rate_limiter.acquire():
        raise TooManyRequestsError(
            f"Rate limit exceeded. Maximum {transition_requests_per_minute} requests per minute allowed."
        )

    from ...workflows.task_execution import TaskExecutionWorkflow

    activity_info = activity.info()
    wf_handle = await get_workflow_handle(handle_id=activity_info.workflow_id)

    # TODO: Filter by last_error type
    if last_error is not None:
        await asyncio.sleep(temporal_activity_after_retry_timeout)
        await wf_handle.signal(
            TaskExecutionWorkflow.set_last_error, LastErrorInput(last_error=None)
        )

    # Load output from blob store if it is a remote object
    transition_info.output = await load_from_blob_store_if_remote(
        transition_info.output
    )

    if not isinstance(context.execution_input, ExecutionInput):
        raise TypeError("Expected ExecutionInput type for context.execution_input")

    # Create transition
    try:
        transition = await create_execution_transition_async(
            developer_id=context.execution_input.developer_id,
            execution_id=context.execution_input.execution.id,
            task_id=context.execution_input.task.id,
            data=transition_info,
            task_token=transition_info.task_token,
            update_execution_status=True,
        )

    except Exception as e:
        if isinstance(e, HTTPException) and cast(HTTPException, e).status_code == 429:
            await wf_handle.signal(
                TaskExecutionWorkflow.set_last_error,
                LastErrorInput(last_error=TooManyRequestsError()),
            )
        raise e

    return transition


original_transition_step = transition_step
mock_transition_step = transition_step

transition_step = activity.defn(name="transition_step")(
    transition_step if not testing else mock_transition_step
)
