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
NON_RETRYABLE_ERROR_TYPES = [
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
    fastapi.exceptions.HTTPException,
    fastapi.exceptions.RequestValidationError,
    httpx.RequestError,
    httpx.HTTPStatusError,
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
    litellm.exceptions.APIError,
]


def is_non_retryable_error(error: Exception) -> bool:
    """
    Determines if the given error is non-retryable.

    This function checks if the error is an instance of any of the error types
    defined in NON_RETRYABLE_ERROR_TYPES.

    Args:
        error (Exception): The error to check.

    Returns:
        bool: True if the error is non-retryable, False otherwise.
    """
    return isinstance(error, tuple(NON_RETRYABLE_ERROR_TYPES))
