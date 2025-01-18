"""
This module defines custom interceptors for Temporal activities and workflows.
The main purpose of these interceptors is to handle errors and prevent retrying
certain types of errors that are known to be non-retryable.
"""

import asyncio
import sys
from collections.abc import Awaitable, Callable, Sequence
from functools import wraps
from typing import Any, NoReturn

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
    WorkflowOutboundInterceptor,
    StartChildWorkflowInput,
    ContinueAsNewInput,
)
from temporalio.workflow import (
    ContinueAsNewError,
    NondeterminismError,
    ReadOnlyContextError,
    ChildWorkflowHandle,
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
    
    if isinstance(obj, (str, bytes, bytearray)):
        # These types already include their content size in getsizeof
        pass
    
    elif isinstance(obj, (tuple, list, set, frozenset)):
        size += sum(get_deep_size(item, seen) for item in obj)
        
    elif isinstance(obj, dict):
        size += sum(get_deep_size(k, seen) + get_deep_size(v, seen) 
                   for k, v in obj.items())
        
    elif hasattr(obj, '__dict__'):
        # Handle custom objects
        size += get_deep_size(obj.__dict__, seen)
        
    elif hasattr(obj, '__slots__'):
        # Handle objects using __slots__
        size += sum(get_deep_size(getattr(obj, attr), seen) 
                   for attr in obj.__slots__ if hasattr(obj, attr))
    
    return size

def is_too_large(result: Any) -> bool:
    return get_deep_size(result) > blob_store_cutoff_kb * 1024


def is_remote_object(arg: Any) -> bool:
    if isinstance(arg, dict):
        return all(k in arg for k in ['key', 'bucket', '_type'])
    return isinstance(arg, RemoteObject)

async def load_if_remote[T](arg: T | RemoteObject[T]) -> T:
    if use_blob_store_for_temporal and is_remote_object(arg):
        return await arg.load()

    return arg


async def offload_if_large[T](result: T) -> T:
    if use_blob_store_for_temporal and is_too_large(result):
        return await RemoteObject.from_value(result)

    return result


async def load_recursive[T](arg: T) -> T:
    """Recursively load remote objects from nested data structures."""
    if is_remote_object(arg):
        return await load_if_remote(arg)
    if isinstance(arg, (list, tuple)):
        return type(arg)(await asyncio.gather(*(load_recursive(item) for item in arg)))
    elif isinstance(arg, dict):
        if is_remote_object(arg):
            return await load_if_remote(arg)
        return {k: await load_recursive(v) for k, v in arg.items()}
    elif isinstance(arg, set):
        return {await load_recursive(item) for item in arg}
    elif hasattr(arg, '__dict__'):
        # Skip immutable objects
        if getattr(arg, '_fields', None) or getattr(arg, '__slots__', None) == ('_state',):  # namedtuple and UUID checks
            return arg
        # Handle custom objects by recursively processing their __dict__
        obj_dict = await load_recursive(arg.__dict__)
        # Create a new instance of the same type
        new_obj = type(arg).__new__(type(arg))
        new_obj.__dict__.update(obj_dict)
        return new_obj
    return arg


def offload_to_blob_store[S, T](
    func: Callable[[S, ExecuteActivityInput | ExecuteWorkflowInput], Awaitable[T]],
) -> Callable[[S, ExecuteActivityInput | ExecuteWorkflowInput], Awaitable[T | RemoteObject[T]]]:
    @wraps(func)
    async def wrapper(
        self,
        input: ExecuteActivityInput | ExecuteWorkflowInput,
    ) -> T | RemoteObject[T]:
        # Load all remote arguments from the blob store
        args: Sequence[Any] = input.args

        input.args = await asyncio.gather(*(load_recursive(arg) for arg in args))
 

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
    async def start_child_workflow(
        self, input: StartChildWorkflowInput
    ) -> ChildWorkflowHandle:

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
