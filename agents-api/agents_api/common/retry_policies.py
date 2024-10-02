from datetime import timedelta

from temporalio.common import RetryPolicy

DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2,
    maximum_attempts=2,
    maximum_interval=timedelta(seconds=10),
    non_retryable_error_types=[
        "WorkflowExecutionAlreadyStarted",
        "TypeError",
        "AssertionError",
        "HTTPException",
        "SyntaxError",
        "ValueError",
    ],
)
