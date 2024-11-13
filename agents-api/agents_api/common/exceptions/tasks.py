"""
🎯 Error Handling: The Art of Knowing When to Try Again

This module is like a bouncer at an error club - it decides which errors get a
second chance and which ones are permanently banned. Some errors are just having
a bad day (like network timeouts), while others are fundamentally problematic
(like trying to divide by zero... seriously, who does that?).

Remember: To err is human, to retry divine... but only if it makes sense!
"""

import asyncio
from typing import cast

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
from tenacity import RetryError

# 🚫 The "No Second Chances" Club - errors that we won't retry
# Because sometimes, no means no!
NON_RETRYABLE_ERROR_TYPES = (
    # Temporal-specific errors (when time itself says no)
    temporalio.exceptions.WorkflowAlreadyStartedError,
    temporalio.exceptions.TerminatedError,
    temporalio.exceptions.CancelledError,
    #
    # Built-in Python exceptions (the classics that never go out of style)
    TypeError,
    AssertionError,
    SyntaxError,
    ValueError,
    ZeroDivisionError,  # Because dividing by zero is still not cool
    IndexError,
    AttributeError,
    LookupError,
    BufferError,
    ArithmeticError,
    KeyError,
    NameError,
    NotImplementedError,
    RecursionError,  # When your code goes down the rabbit hole too deep
    RuntimeError,
    StopIteration,
    StopAsyncIteration,
    IndentationError,  # Spaces vs tabs: the eternal debate
    TabError,
    #
    # Unicode-related errors (when characters misbehave)
    UnicodeError,
    UnicodeEncodeError,
    UnicodeDecodeError,
    UnicodeTranslateError,
    #
    # HTTP and API-related errors (when the web says "nope")
    fastapi.exceptions.RequestValidationError,
    #
    # Asynchronous programming errors (async/await gone wrong)
    asyncio.CancelledError,
    asyncio.InvalidStateError,
    GeneratorExit,
    #
    # Third-party library exceptions (when other people's code says no)
    jinja2.exceptions.TemplateSyntaxError,
    jinja2.exceptions.TemplateNotFound,
    jsonschema.exceptions.ValidationError,
    pydantic.ValidationError,
    requests.exceptions.InvalidURL,
    requests.exceptions.MissingSchema,
    #
    # Box exceptions (when your box is broken)
    box.exceptions.BoxKeyError,
    box.exceptions.BoxTypeError,
    box.exceptions.BoxValueError,
    #
    # Beartype exceptions (when your types are unbearable)
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
    # LiteLLM exceptions (when AI has a bad day)
    litellm.exceptions.NotFoundError,
    litellm.exceptions.InvalidRequestError,
    litellm.exceptions.AuthenticationError,
    litellm.exceptions.ServiceUnavailableError,
    litellm.exceptions.OpenAIError,
)

# 🔄 The "Try Again" Club - errors that deserve another shot
# Because everyone deserves a second chance... or third... or fourth...
RETRYABLE_ERROR_TYPES = (
    # LiteLLM exceptions (when AI needs a coffee break)
    litellm.exceptions.RateLimitError,
    litellm.exceptions.APIError,  # Added to retry on "APIError: OpenAIException - Connection error"
    #
    # HTTP/Network related errors (internet having a bad hair day)
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
    # Standard library errors that are typically transient (like a bad mood)
    ConnectionError,
    TimeoutError,
    OSError,  # Covers many IO-related errors that may be transient
    IOError,
    #
    # Database/storage related (when the database needs a nap)
    asyncio.TimeoutError,
    #
    # Tenacity exceptions (retry when retrying goes wrong lol)
    RetryError,
)

# HTTP status codes that say "maybe try again later?"
RETRYABLE_HTTP_STATUS_CODES = (
    408,  # Request Timeout (server needs a coffee break)
    429,  # Too Many Requests (slow down, speedster!)
    503,  # Service Unavailable (server is having a moment)
    504,  # Gateway Timeout (the internet took a detour)
)


def is_retryable_error(error: BaseException) -> bool:
    """
    The Great Error Judge: Decides if an error deserves another chance at life.

    Think of this function as a very understanding but firm teacher - some mistakes
    get a do-over, others are learning opportunities (aka failures).

    Args:
        error (Exception): The error that's pleading its case

    Returns:
        bool: True if the error gets another shot, False if it's game over
    """
    # First, check if it's in the "permanently banned" list
    if isinstance(error, NON_RETRYABLE_ERROR_TYPES):
        return False

    # Check if it's in the "VIP retry club"
    if isinstance(error, RETRYABLE_ERROR_TYPES):
        return True

    # Special handling for HTTP errors (because they're special snowflakes)
    if isinstance(error, fastapi.exceptions.HTTPException):
        error = cast(fastapi.exceptions.HTTPException, error)
        if error.status_code in RETRYABLE_HTTP_STATUS_CODES:
            return True

    if isinstance(error, httpx.HTTPStatusError):
        error = cast(httpx.HTTPStatusError, error)
        if error.response.status_code in RETRYABLE_HTTP_STATUS_CODES:
            return True

    # If we don't know this error, we play it safe and don't retry
    # (stranger danger!)
    return False
