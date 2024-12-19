"""
This module defines custom interceptors for Temporal activities and workflows.
The main purpose of these interceptors is to handle errors and prevent retrying
certain types of errors that are known to be non-retryable.
"""

import asyncio
import sys
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, Sequence, Type

from temporalio import workflow
from temporalio.activity import _CompleteAsyncError as CompleteAsyncError
from temporalio.exceptions import ApplicationError, FailureError, TemporalError
from temporalio.service import RPCError
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    ExecuteWorkflowInput,
    Interceptor,
    WorkflowInboundInterceptor,
    WorkflowInterceptorClassInput,
)
from temporalio.workflow import (
    ContinueAsNewError,
    NondeterminismError,
    ReadOnlyContextError,
)

with workflow.unsafe.imports_passed_through():
    from ..env import blob_store_cutoff_kb, use_blob_store_for_temporal
    from .exceptions.tasks import is_retryable_error
    from .protocol.remote import RemoteObject

# Common exceptions that should be re-raised without modification
PASSTHROUGH_EXCEPTIONS = (
    ContinueAsNewError,
    ReadOnlyContextError,
    NondeterminismError,
    RPCError,
    CompleteAsyncError,
    TemporalError,
    FailureError,
    ApplicationError,
)


def is_too_large(result: Any) -> bool:
    return sys.getsizeof(result) > blob_store_cutoff_kb * 1024


async def load_if_remote[T](arg: T | RemoteObject[T]) -> T:
    if use_blob_store_for_temporal and isinstance(arg, RemoteObject):
        return await arg.load()

    return arg


async def offload_if_large[T](result: T) -> T:
    if use_blob_store_for_temporal and is_too_large(result):
        return await RemoteObject.from_value(result)

    return result


def offload_to_blob_store[S, T](
    func: Callable[[S, ExecuteActivityInput | ExecuteWorkflowInput], Awaitable[T]],
) -> Callable[
    [S, ExecuteActivityInput | ExecuteWorkflowInput], Awaitable[T | RemoteObject[T]]
]:
    @wraps(func)
    async def wrapper(
        self,
        input: ExecuteActivityInput | ExecuteWorkflowInput,
    ) -> T | RemoteObject[T]:
        # Load all remote arguments from the blob store
        args: Sequence[Any] = input.args

        if use_blob_store_for_temporal:
            input.args = await asyncio.gather(*[load_if_remote(arg) for arg in args])

        # Execute the function
        result = await func(self, input)

        # Save the result to the blob store if necessary
        return await offload_if_large(result)

    return wrapper


async def handle_execution_with_errors[I, T](
    execution_fn: Callable[[I], Awaitable[T]],
    input: I,
) -> T:
    """
    Common error handling logic for both activities and workflows.

    Args:
        execution_fn: Async function to execute with error handling
        input: Input to the execution function

    Returns:
        The result of the execution function

    Raises:
        ApplicationError: For non-retryable errors
        Any other exception: For retryable errors
    """
    try:
        return await execution_fn(input)
    except PASSTHROUGH_EXCEPTIONS:
        raise
    except BaseException as e:
        if not is_retryable_error(e):
            raise ApplicationError(
                str(e),
                type=type(e).__name__,
                non_retryable=True,
            )
        raise


class CustomActivityInterceptor(ActivityInboundInterceptor):
    """
    Custom interceptor for Temporal activities.

    This interceptor catches exceptions during activity execution and
    raises them as non-retryable ApplicationErrors if they are identified
    as non-retryable errors.
    """

    @offload_to_blob_store
    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        """
        Handles activity execution by intercepting errors and determining their retry behavior.
        """
        return await handle_execution_with_errors(
            super().execute_activity,
            input,
        )


class CustomWorkflowInterceptor(WorkflowInboundInterceptor):
    """
    Custom interceptor for Temporal workflows.

    Handles workflow execution errors and determines their retry behavior.
    """

    @offload_to_blob_store
    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        """
        Executes workflows and handles error cases appropriately.
        """
        return await handle_execution_with_errors(
            super().execute_workflow,
            input,
        )


class CustomInterceptor(Interceptor):
    """
    Main interceptor class that provides both activity and workflow interceptors.
    """

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        """
        Creates and returns a custom activity interceptor.
        """
        return CustomActivityInterceptor(super().intercept_activity(next))

    def workflow_interceptor_class(
        self, input: WorkflowInterceptorClassInput
    ) -> Optional[Type[WorkflowInboundInterceptor]]:
        """
        Returns the custom workflow interceptor class.
        """
        return CustomWorkflowInterceptor
