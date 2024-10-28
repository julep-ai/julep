"""
This module defines non-retryable error types and provides a function to check
if a given error is non-retryable. These are used in conjunction with custom
Temporal interceptors to prevent unnecessary retries of certain error types.
"""

import asyncio

import beartype
import beartype.roar
import box
import box.exceptions
import fastapi
import httpx
import jinja2
import jsonschema.exceptions
import litellm
import pydantic
import requests
import temporalio.exceptions

# List of error types that should not be retried
NON_RETRYABLE_ERROR_TYPES = (
    # Temporal-specific errors
    temporalio.exceptions.WorkflowAlreadyStartedError,
    temporalio.exceptions.TerminatedError,
    temporalio.exceptions.CancelledError,
    #
    # Built-in Python exceptions
    TypeError,
    AssertionError,
    SyntaxError,
    ValueError,
    ZeroDivisionError,
    IndexError,
    AttributeError,
    LookupError,
    BufferError,
    ArithmeticError,
    KeyError,
    NameError,
    NotImplementedError,
    RecursionError,
    RuntimeError,
    StopIteration,
    StopAsyncIteration,
    IndentationError,
    TabError,
    #
    # Unicode-related errors
    UnicodeError,
    UnicodeEncodeError,
    UnicodeDecodeError,
    UnicodeTranslateError,
    #
    # HTTP and API-related errors
    fastapi.exceptions.RequestValidationError,
    #
    # Asynchronous programming errors
    asyncio.CancelledError,
    asyncio.InvalidStateError,
    GeneratorExit,
    #
    # Third-party library exceptions
    jinja2.exceptions.TemplateSyntaxError,
    jinja2.exceptions.TemplateNotFound,
    jsonschema.exceptions.ValidationError,
    pydantic.ValidationError,
    requests.exceptions.InvalidURL,
    requests.exceptions.MissingSchema,
    #
    # Box exceptions
    box.exceptions.BoxKeyError,
    box.exceptions.BoxTypeError,
    box.exceptions.BoxValueError,
    #
    # Beartype exceptions
    beartype.roar.BeartypeException,
    beartype.roar.BeartypeDecorException,
    beartype.roar.BeartypeDecorHintException,
    beartype.roar.BeartypeDecorHintNonpepException,
    beartype.roar.BeartypeDecorHintPepException,
    beartype.roar.BeartypeDecorHintPepUnsupportedException,
    beartype.roar.BeartypeDecorHintTypeException,
    beartype.roar.BeartypeDecorParamException,
    beartype.roar.BeartypeDecorParamNameException,
    beartype.roar.BeartypeCallHintParamViolation,
    beartype.roar.BeartypeCallHintReturnViolation,
    beartype.roar.BeartypeDecorHintParamDefaultViolation,
    beartype.roar.BeartypeDoorHintViolation,
    #
    # LiteLLM exceptions
    litellm.exceptions.NotFoundError,
    litellm.exceptions.InvalidRequestError,
    litellm.exceptions.AuthenticationError,
    litellm.exceptions.ServiceUnavailableError,
    litellm.exceptions.OpenAIError,
)

RETRYABLE_ERROR_TYPES = (
    # LiteLLM exceptions
    litellm.exceptions.RateLimitError,
    litellm.exceptions.APIError,  # Added to retry on "APIError: OpenAIException - Connection error"
    #
    # HTTP/Network related errors
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ConnectTimeout,
    requests.exceptions.ReadTimeout,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    #
    # Standard library errors that are typically transient
    ConnectionError,
    TimeoutError,
    OSError,  # Covers many IO-related errors that may be transient
    IOError,
    #
    # Database/storage related
    asyncio.TimeoutError,
)

RETRYABLE_HTTP_STATUS_CODES = (408, 429, 503, 504)


def is_retryable_error(error: BaseException) -> bool:
    """
    Determines if the given error should be retried or not.

    Args:
        error (Exception): The error to check.

    Returns:
        bool: True if the error is retryable, False otherwise.
    """

    if isinstance(error, NON_RETRYABLE_ERROR_TYPES):
        return False

    if isinstance(error, RETRYABLE_ERROR_TYPES):
        return True

    # Check for specific HTTP errors that should be retried
    if isinstance(error, fastapi.exceptions.HTTPException):
        if error.status_code in RETRYABLE_HTTP_STATUS_CODES:
            return True

    if isinstance(error, httpx.HTTPStatusError):
        if error.response.status_code in RETRYABLE_HTTP_STATUS_CODES:
            return True

    # If we don't know about the error, we should not retry
    return False
