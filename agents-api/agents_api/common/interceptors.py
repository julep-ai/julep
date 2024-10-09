"""
This module defines custom interceptors for Temporal activities and workflows.
The main purpose of these interceptors is to handle errors and prevent retrying
certain types of errors that are known to be non-retryable.
"""

from typing import Optional, Type

from temporalio.exceptions import ApplicationError
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    ExecuteWorkflowInput,
    Interceptor,
    WorkflowInboundInterceptor,
    WorkflowInterceptorClassInput,
)

from .exceptions.tasks import is_non_retryable_error


class CustomActivityInterceptor(ActivityInboundInterceptor):
    """
    Custom interceptor for Temporal activities.

    This interceptor catches exceptions during activity execution and
    raises them as non-retryable ApplicationErrors if they are identified
    as non-retryable errors.
    """

    async def execute_activity(self, input: ExecuteActivityInput):
        try:
            return await super().execute_activity(input)
        except Exception as e:
            if is_non_retryable_error(e):
                raise ApplicationError(
                    str(e),
                    type=type(e).__name__,
                    non_retryable=True,
                )
            raise


class CustomWorkflowInterceptor(WorkflowInboundInterceptor):
    """
    Custom interceptor for Temporal workflows.

    This interceptor catches exceptions during workflow execution and
    raises them as non-retryable ApplicationErrors if they are identified
    as non-retryable errors.
    """

    async def execute_workflow(self, input: ExecuteWorkflowInput):
        try:
            return await super().execute_workflow(input)
        except Exception as e:
            if is_non_retryable_error(e):
                raise ApplicationError(
                    str(e),
                    type=type(e).__name__,
                    non_retryable=True,
                )
            raise


class CustomInterceptor(Interceptor):
    """
    Custom Interceptor that combines both activity and workflow interceptors.

    This class is responsible for creating and returning the custom
    interceptors for both activities and workflows.
    """

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        """
        Creates and returns a CustomActivityInterceptor.

        This method is called by Temporal to intercept activity executions.
        """
        return CustomActivityInterceptor(super().intercept_activity(next))

    def workflow_interceptor_class(
        self, input: WorkflowInterceptorClassInput
    ) -> Optional[Type[WorkflowInboundInterceptor]]:
        """
        Returns the CustomWorkflowInterceptor class.

        This method is called by Temporal to get the workflow interceptor class.
        """
        return CustomWorkflowInterceptor
