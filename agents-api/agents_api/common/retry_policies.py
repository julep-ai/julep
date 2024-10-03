from datetime import timedelta

from temporalio.common import RetryPolicy

DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2,
    maximum_attempts=25,
    maximum_interval=timedelta(seconds=300),
    non_retryable_error_types=[
        # Temporal-specific errors
        "WorkflowExecutionAlreadyStarted",
        "temporalio.exceptions.TerminalFailure",
        "temporalio.exceptions.CanceledError",
        #
        # Built-in Python exceptions
        "TypeError",
        "AssertionError",
        "SyntaxError",
        "ValueError",
        "ZeroDivisionError",
        "IndexError",
        "AttributeError",
        "LookupError",
        "BufferError",
        "ArithmeticError",
        "KeyError",
        "NameError",
        "NotImplementedError",
        "RecursionError",
        "RuntimeError",
        "StopIteration",
        "StopAsyncIteration",
        "IndentationError",
        "TabError",
        #
        # Unicode-related errors
        "UnicodeError",
        "UnicodeEncodeError",
        "UnicodeDecodeError",
        "UnicodeTranslateError",
        #
        # HTTP and API-related errors
        "HTTPException",
        "fastapi.exceptions.HTTPException",
        "fastapi.exceptions.RequestValidationError",
        "httpx.RequestError",
        "httpx.HTTPStatusError",
        #
        # Asynchronous programming errors
        "asyncio.CancelledError",
        "asyncio.InvalidStateError",
        "GeneratorExit",
        #
        # Third-party library exceptions
        "jinja2.exceptions.TemplateSyntaxError",
        "jinja2.exceptions.TemplateNotFound",
        "jsonschema.exceptions.ValidationError",
        "pydantic.ValidationError",
        "requests.exceptions.InvalidURL",
        "requests.exceptions.MissingSchema",
    ],
)
