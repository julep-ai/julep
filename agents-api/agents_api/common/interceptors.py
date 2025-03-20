"""
This module defines custom interceptors for Temporal activities and workflows.
The main purpose of these interceptors is to handle errors and prevent retrying
certain types of errors that are known to be non-retryable.
"""

import inspect
from asyncio.exceptions import CancelledError as AsyncioCancelledError
from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from typing import Any

from temporalio import workflow
from temporalio.activity import _CompleteAsyncError as CompleteAsyncError
from temporalio.client import (
    Interceptor as ClientInterceptor,
)
from temporalio.client import (
    OutboundInterceptor,
    StartWorkflowInput,
    WorkflowHandle,
)
from temporalio.exceptions import ActivityError, ApplicationError, FailureError, TemporalError
from temporalio.service import RPCError
from temporalio.worker import (
    ActivityInboundInterceptor,
    ContinueAsNewInput,
    ExecuteActivityInput,
    ExecuteWorkflowInput,
    Interceptor,
    StartActivityInput,
    StartChildWorkflowInput,
    StartLocalActivityInput,
    WorkflowInboundInterceptor,
    WorkflowInterceptorClassInput,
    WorkflowOutboundInterceptor,
)
from temporalio.workflow import (
    ActivityHandle,
    ChildWorkflowHandle,
    ContinueAsNewError,
    NondeterminismError,
    NoReturn,
    ReadOnlyContextError,
)

with workflow.unsafe.imports_passed_through():
    from ..env import blob_store_cutoff_kb, use_blob_store_for_temporal
    from ..worker.codec import RemoteObject
    from .exceptions.tasks import is_retryable_error
    from .protocol.tasks import ExecutionInput, StepContext, StepOutcome
    from .utils.memory import total_size

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
    AsyncioCancelledError,
)


def is_too_large(result: Any) -> bool:
    """
    Determine if an object exceeds the size cutoff threshold.

    Args:
        result: The object to check

    Returns:
        True if the object is larger than the cutoff threshold, False otherwise
    """
    return total_size(result) > blob_store_cutoff_kb * 1024


def load_if_remote(arg: Any | RemoteObject) -> Any:
    if not use_blob_store_for_temporal:
        return arg

    if isinstance(arg, ChildWorkflowHandle):
        return arg

    if isinstance(arg, RemoteObject):
        return arg.load()

    if isinstance(arg, StepContext):
        arg.load_inputs()

    elif isinstance(arg, StepOutcome):
        arg.load_remote()

    elif isinstance(arg, ExecutionInput):
        arg.load_arguments()

    return arg


def offload_if_large[T](result: T) -> T | RemoteObject:
    if not use_blob_store_for_temporal:
        return result

    if isinstance(result, ChildWorkflowHandle):
        return result

    if isinstance(result, ActivityHandle):
        return result

    if is_too_large(result):
        return RemoteObject.from_value(result)

    return result


def offload_to_blob_store[S, T](
    func: Callable[[S, ExecuteActivityInput | ExecuteWorkflowInput], Awaitable[T]],
) -> Callable[[S, ExecuteActivityInput | ExecuteWorkflowInput], Awaitable[T | RemoteObject]]:
    @wraps(func)
    async def wrapper(
        self,
        input: ExecuteActivityInput | ExecuteWorkflowInput,
    ) -> T | RemoteObject:
        # Load all remote arguments from the blob store
        args: Sequence[Any] = input.args

        if use_blob_store_for_temporal:
            input.args = [load_if_remote(arg) for arg in args]

        # Execute the function
        result = await func(self, input)

        # Save the result to the blob store if necessary
        return offload_if_large(result)

    @wraps(func)
    def wrapper_sync(
        self,
        input: ExecuteActivityInput | ExecuteWorkflowInput,
    ) -> T | RemoteObject:
        # Load all remote arguments from the blob store
        args: Sequence[Any] = input.args

        if use_blob_store_for_temporal:
            input.args = [load_if_remote(arg) for arg in args]

        # Execute the function
        result = func(self, input)

        # Save the result to the blob store if necessary
        return offload_if_large(result)

    if inspect.iscoroutinefunction(func):
        return wrapper
    return wrapper_sync


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


def handle_execution_with_errors_sync[I, T](
    execution_fn: Callable[[I], T],
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
        return execution_fn(input)
    except PASSTHROUGH_EXCEPTIONS:
        raise
    except BaseException as e:
        while isinstance(e, ActivityError) and getattr(e, "__cause__", None):
            e = e.__cause__
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

    def init(self, outbound: WorkflowOutboundInterceptor) -> None:
        """Initialize with an outbound interceptor.

        To add a custom outbound interceptor, wrap the given interceptor before
        sending to the next ``init`` call.
        """
        self.next.init(CustomWorkflowOutboundInterceptor(outbound))

    @offload_to_blob_store
    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        """
        Executes workflows and handles error cases appropriately.
        """
        return await handle_execution_with_errors(
            super().execute_workflow,
            input,
        )


class CustomWorkflowOutboundInterceptor(WorkflowOutboundInterceptor):
    """
    Custom outbound interceptor for Temporal workflows.
    """

    # @offload_to_blob_store
    def start_activity(self, input: StartActivityInput) -> ActivityHandle:
        input.args = [offload_if_large(arg) for arg in input.args]
        return handle_execution_with_errors_sync(
            super().start_activity,
            input,
        )

    @offload_to_blob_store
    def continue_as_new(self, input: ContinueAsNewInput) -> NoReturn:
        return handle_execution_with_errors_sync(
            super().continue_as_new,
            input,
        )

    @offload_to_blob_store
    def start_local_activity(self, input: StartLocalActivityInput) -> ActivityHandle:
        return handle_execution_with_errors_sync(
            super().start_local_activity,
            input,
        )

    # @offload_to_blob_store
    async def start_child_workflow(self, input: StartChildWorkflowInput) -> ChildWorkflowHandle:
        input.args = [offload_if_large(arg) for arg in input.args]
        return await handle_execution_with_errors(
            super().start_child_workflow,
            input,
        )


class CustomInterceptor(Interceptor):
    """
    Main interceptor class that provides both activity and workflow interceptors.
    """

    def intercept_activity(
        self,
        next: ActivityInboundInterceptor,
    ) -> ActivityInboundInterceptor:
        """
        Creates and returns a custom activity interceptor.
        """
        return CustomActivityInterceptor(super().intercept_activity(next))

    def workflow_interceptor_class(
        self,
        input: WorkflowInterceptorClassInput,
    ) -> type[WorkflowInboundInterceptor] | None:
        """
        Returns the custom workflow interceptor class.
        """
        return CustomWorkflowInterceptor


class CustomClientInterceptor(ClientInterceptor):
    """
    Custom interceptor for Temporal.
    """

    def intercept_client(self, next: OutboundInterceptor) -> OutboundInterceptor:
        return CustomOutboundInterceptor(super().intercept_client(next))


class CustomOutboundInterceptor(OutboundInterceptor):
    """
    Custom outbound interceptor for Temporal workflows.
    """

    # @offload_to_blob_store
    async def start_workflow(self, input: StartWorkflowInput) -> WorkflowHandle[Any, Any]:
        """
        interceptor for outbound workflow calls
        """
        input.args = [offload_if_large(arg) for arg in input.args]
        return await handle_execution_with_errors(
            super().start_workflow,
            input,
        )
