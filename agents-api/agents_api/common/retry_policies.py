from datetime import timedelta

from temporalio.common import RetryPolicy
from ..env import debug, testing
DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2,
    maximum_attempts=2 if debug or testing else 25,
    maximum_interval=timedelta(seconds=10) if debug or testing else timedelta(seconds=300),
    non_retryable_error_types=[
        "WorkflowExecutionAlreadyStarted",
        "TypeError",
        "AssertionError",
        "HTTPException",
        "SyntaxError",
        "ValueError",
        "ZeroDivisionError",
        "jinja2.exceptions.TemplateSyntaxError",
        "jinja2.exceptions.TemplateNotFound",
        "jsonschema.exceptions.ValidationError",
        "pydantic.ValidationError",
        "asyncio.CancelledError",
        "asyncio.InvalidStateError",
        "requests.exceptions.InvalidURL",
        "requests.exceptions.MissingSchema",
        "temporalio.exceptions.TerminalFailure",
        "temporalio.exceptions.CanceledError",
        "fastapi.exceptions.HTTPException",
        "fastapi.exceptions.RequestValidationError",
        "httpx.RequestError",
        "httpx.HTTPStatusError",
    ],
)
