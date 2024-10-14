# from datetime import timedelta

# from temporalio.common import RetryPolicy

# DEFAULT_RETRY_POLICY = RetryPolicy(
#     initial_interval=timedelta(seconds=1),
#     backoff_coefficient=2,
#     maximum_attempts=25,
#     maximum_interval=timedelta(seconds=300),
# )

# FIXME: Adding both interceptors and retry policy (even with `non_retryable_errors` not set)
# is causing the errors to be retried. We need to find a workaround for this.
DEFAULT_RETRY_POLICY = None
