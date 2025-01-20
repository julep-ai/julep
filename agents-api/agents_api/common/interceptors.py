"""
This module defines custom interceptors for Temporal activities and workflows.
The main purpose of these interceptors is to handle errors and prevent retrying
certain types of errors that are known to be non-retryable.
"""

import sys
from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from typing import Any

from temporalio import workflow
from temporalio.activity import _CompleteAsyncError as CompleteAsyncError
from temporalio.exceptions import ApplicationError, FailureError, TemporalError
from temporalio.service import RPCError
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    ExecuteWorkflowInput,
    Interceptor,
    StartChildWorkflowInput,
    WorkflowInboundInterceptor,
    WorkflowInterceptorClassInput,
    WorkflowOutboundInterceptor,
)
from temporalio.workflow import (
    ChildWorkflowHandle,
    ContinueAsNewError,
    NondeterminismError,
    ReadOnlyContextError,
)

with workflow.unsafe.imports_passed_through():
    from ..env import blob_store_cutoff_kb, use_blob_store_for_temporal
    from .exceptions.tasks import is_retryable_error
    from .protocol.remote import RemoteObject
    from .protocol.tasks import ExecutionInput, StepContext, StepOutcome

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


def get_deep_size(obj: Any, seen: set | None = None) -> int:
    """
    Recursively calculate total size of an object and all its contents in bytes.

    Args:
        obj: The object to measure
        seen: Set of object ids already processed to handle circular references

    Returns:
        Total size in bytes
    """
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, str | bytes | bytearray):
        # These types already include their content size in getsizeof
        pass

    elif isinstance(obj, tuple | list | set | frozenset):
        size += sum(get_deep_size(item, seen) for item in obj)

    elif isinstance(obj, dict):
        size += sum(get_deep_size(k, seen) + get_deep_size(v, seen) for k, v in obj.items())

    elif hasattr(obj, "__dict__"):
        # Handle custom objects
        size += get_deep_size(obj.__dict__, seen)

    elif hasattr(obj, "__slots__"):
        # Handle objects using __slots__
        size += sum(
            get_deep_size(getattr(obj, attr), seen)
            for attr in obj.__slots__
            if hasattr(obj, attr)
        )

    return size


def is_too_large(result: Any) -> bool:
    return get_deep_size(result) > blob_store_cutoff_kb * 1024


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
        arg.load_transition_to()

    elif isinstance(arg, ExecutionInput):
        arg.load_arguments()

    return arg


def offload_if_large[T](result: T) -> T | RemoteObject:
    if not use_blob_store_for_temporal:
        return result

    if isinstance(result, ChildWorkflowHandle):
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

    def init(self, outbound: WorkflowOutboundInterceptor) -> None:
        """Initialize with an outbound interceptor.

        To add a custom outbound interceptor, wrap the given interceptor before
        sending to the next ``init`` call.
        """
        self.next.init(CustomOutboundInterceptor(outbound))

    @offload_to_blob_store
    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        """
        Executes workflows and handles error cases appropriately.
        """
        return await handle_execution_with_errors(
            super().execute_workflow,
            input,
        )


class CustomOutboundInterceptor(WorkflowOutboundInterceptor):
    """
    Custom outbound interceptor for Temporal workflows.
    """

    @offload_to_blob_store
    async def start_child_workflow(self, input: StartChildWorkflowInput) -> ChildWorkflowHandle:
        return await handle_execution_with_errors(
            super().start_child_workflow,
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
    ) -> type[WorkflowInboundInterceptor] | None:
        """
        Returns the custom workflow interceptor class.
        """
        return CustomWorkflowInterceptor
