"""
This module defines custom interceptors for Temporal activities and workflows.
The main purpose of these interceptors is to handle errors and prevent retrying
certain types of errors that are known to be non-retryable.
"""

from typing import Optional, Type

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

from .exceptions.tasks import is_retryable_error


class CustomActivityInterceptor(ActivityInboundInterceptor):
    """
    Custom interceptor for Temporal activities.

    This interceptor catches exceptions during activity execution and
    raises them as non-retryable ApplicationErrors if they are identified
    as non-retryable errors.
    """

    async def execute_activity(self, input: ExecuteActivityInput):
        """
        🎭 The Activity Whisperer: Handles activity execution with style and grace

        This is like a safety net for your activities - catching errors and deciding
        their fate with the wisdom of a fortune cookie.
        """
        try:
            return await super().execute_activity(input)
        except (
            ContinueAsNewError,  # When you need a fresh start
            ReadOnlyContextError,  # When someone tries to write in a museum
            NondeterminismError,  # When chaos theory kicks in
            RPCError,  # When computers can't talk to each other
            CompleteAsyncError,  # When async goes wrong
            TemporalError,  # When time itself rebels
            FailureError,  # When failure is not an option, but happens anyway
            ApplicationError,  # When the app says "nope"
        ):
            raise
        except BaseException as e:
            if not is_retryable_error(e):
                # If it's not retryable, we wrap it in a nice bow (ApplicationError)
                # and mark it as non-retryable to prevent further attempts
                raise ApplicationError(
                    str(e),
                    type=type(e).__name__,
                    non_retryable=True,
                )
            # For retryable errors, we'll let Temporal retry with backoff
            # Default retry policy ensures at least 2 retries
            raise


class CustomWorkflowInterceptor(WorkflowInboundInterceptor):
    """
    🎪 The Workflow Circus Ringmaster

    This interceptor is like a circus ringmaster - keeping all the workflow acts
    running smoothly and catching any lions (errors) that escape their cages.
    """

    async def execute_workflow(self, input: ExecuteWorkflowInput):
        """
        🎪 The Main Event: Workflow Execution Extravaganza!

        Watch as we gracefully handle errors like a trapeze artist catching their partner!
        """
        try:
            return await super().execute_workflow(input)
        except (
            ContinueAsNewError,  # The show must go on!
            ReadOnlyContextError,  # No touching, please!
            NondeterminismError,  # When butterflies cause hurricanes
            RPCError,  # Lost in translation
            CompleteAsyncError,  # Async said "bye" too soon
            TemporalError,  # Time is relative, errors are absolute
            FailureError,  # Task failed successfully
            ApplicationError,  # App.exe has stopped working
        ):
            raise
        except BaseException as e:
            if not is_retryable_error(e):
                # Pack the error in a nice box with a "do not retry" sticker
                raise ApplicationError(
                    str(e),
                    type=type(e).__name__,
                    non_retryable=True,
                )
            # Let it retry - everyone deserves a second (or third) chance!
            raise


class CustomInterceptor(Interceptor):
    """
    🎭 The Grand Interceptor: Master of Ceremonies

    This is like the backstage manager of a theater - making sure both the
    activity actors and workflow directors have their interceptor costumes on.
    """

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        """
        🎬 Activity Interceptor Factory: Where the magic begins!

        Creating custom activity interceptors faster than a caffeinated barista
        makes espresso shots.
        """
        return CustomActivityInterceptor(super().intercept_activity(next))

    def workflow_interceptor_class(
        self, input: WorkflowInterceptorClassInput
    ) -> Optional[Type[WorkflowInboundInterceptor]]:
        """
        🎪 Workflow Interceptor Class Selector

        Like a matchmaker for workflows and their interceptors - a match made in
        exception handling heaven!
        """
        return CustomWorkflowInterceptor
