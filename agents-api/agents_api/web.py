"""
This module initializes the FastAPI application, registers routes, sets up middleware, and configures exception handlers.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any, cast

import sentry_sdk
import uvicorn
import uvloop
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from litellm.exceptions import APIError
from pydantic import ValidationError
from temporalio.service import RPCError

from .app import app
from .common.exceptions import BaseCommonException
from .dependencies.auth import get_api_key
from .env import enable_responses, sentry_dsn
from .exceptions import PromptTooBigError
from .routers import (
    agents,
    docs,
    files,
    healthz,
    internal,
    jobs,
    responses,
    sessions,
    tasks,
    users,
)

if not sentry_dsn:
    print("Sentry DSN not found. Sentry will not be enabled.")
else:
    sentry_sdk.init(
        dsn=sentry_dsn,
        enable_tracing=True,
        traces_sample_rate=1.0,
    )


logger: logging.Logger = logging.getLogger(__name__)


def make_exception_handler(status_code: int) -> Callable[[Any, Any], Any]:
    """
    Creates a custom exception handler for the application.

    Parameters:
    - status_code (int): The HTTP status code to return for this exception.

    Returns:
    A callable exception handler that logs the exception and returns a JSON response with the specified status code.
    """

    async def _handler(request: Request, exc: Exception):
        if isinstance(exc, ValidationError | RequestValidationError):
            exc = cast(ValidationError | RequestValidationError, exc)
            error_details = []

            # Process each validation error
            for error in exc.errors():
                error_info = {
                    "type": error.get("type", "validation_error"),
                    "msg": error.get("msg", "Validation error"),
                    "loc": _format_location(error.get("loc", [])),
                }

                # Enhance with fixes/suggestions when possible
                error_info.update(_get_error_suggestions(error))

                # Add input value if available
                if "input" in error:
                    error_info["received"] = str(error["input"])

                error_details.append(error_info)

            # Log the error with appropriate level
            logger.warning(f"Validation error: {error_details}")

            return JSONResponse(
                content={
                    "error": {
                        "message": "Validation error",
                        "details": error_details,
                        "code": "validation_error",
                    }
                },
                status_code=status_code,
            )

        # For non-validation errors, return a simpler error response
        return JSONResponse(
            content={
                "error": {
                    "message": str(exc),
                    "code": getattr(exc, "code", "unknown_error"),
                }
            },
            status_code=status_code,
        )

    return _handler


def _format_location(loc: list) -> str:
    """Format error location into a human-readable string."""
    if not loc:
        return ""

    # Skip the initial 'body' element if present
    if loc[0] == "body" and len(loc) > 1:
        loc = loc[1:]

    # Format the location
    parts = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            if parts:  # Add dot separator if not first element
                parts.append(f".{item}")
            else:
                parts.append(str(item))

    return "".join(parts)


def _get_error_suggestions(error: dict) -> dict:
    """Generate user-friendly suggestions based on the error type."""
    error_type = error.get("type", "")
    suggestions = {}

    # Handle different validation error types
    if error_type == "missing":
        suggestions["fix"] = "Add this required field to your request"
        suggestions["example"] = '{ "field_name": "value" }'

    elif error_type == "type_error":
        if "expected_type" in error:
            suggestions["fix"] = f"Provide a value of type {error['expected_type']}"
            if error["expected_type"] == "string":
                suggestions["example"] = '"text value"'
            elif error["expected_type"] == "integer":
                suggestions["example"] = "42"
            elif error["expected_type"] == "number":
                suggestions["example"] = "3.14"
            elif error["expected_type"] == "boolean":
                suggestions["example"] = "true"
            elif error["expected_type"] == "array":
                suggestions["example"] = "[]"
            elif error["expected_type"] == "object":
                suggestions["example"] = "{}"
        else:
            suggestions["fix"] = "Provide a value of the correct type"

    elif error_type == "value_error.missing":
        suggestions["fix"] = "Provide a value for this required field"
        suggestions["note"] = "This field cannot be null or undefined"

    elif error_type == "value_error.extra":
        suggestions["fix"] = "Remove this field as it is not expected"
        suggestions["note"] = "Check the API documentation for the correct field names"

    elif error_type == "value_error.const":
        if "permitted" in error:
            suggestions["fix"] = f"Value must be one of: {error['permitted']}"
            suggestions["example"] = (
                f"{error['permitted'][0] if error['permitted'] else 'appropriate_value'}"
            )

    elif "min_length" in error_type:
        if "limit_value" in error:
            suggestions["fix"] = f"Value must have at least {error['limit_value']} characters"
            try:
                limit = int(error["limit_value"])
                suggestions["example"] = "x" * limit
            except (ValueError, TypeError):
                suggestions["example"] = "x" * 5  # Fallback example

    elif "max_length" in error_type:
        if "limit_value" in error:
            suggestions["fix"] = f"Value must have at most {error['limit_value']} characters"
            suggestions["note"] = (
                f"Current value exceeds the maximum length of {error['limit_value']} characters"
            )

    # This case is now handled by the more general "min_length" check above

    # This case is now handled by the more general "max_length" check above

    elif "not_ge" in error_type:
        if "limit_value" in error:
            suggestions["fix"] = (
                f"Value must be greater than or equal to {error['limit_value']}"
            )
            suggestions["example"] = f"{error['limit_value']}"

    elif "not_le" in error_type:
        if "limit_value" in error:
            suggestions["fix"] = f"Value must be less than or equal to {error['limit_value']}"
            suggestions["example"] = f"{error['limit_value']}"

    elif "not_gt" in error_type:
        if "limit_value" in error:
            suggestions["fix"] = f"Value must be greater than {error['limit_value']}"
            try:
                suggestions["example"] = f"{float(error['limit_value']) + 1}"
            except (ValueError, TypeError):
                suggestions["example"] = "a value greater than the limit"

    elif "not_lt" in error_type:
        if "limit_value" in error:
            suggestions["fix"] = f"Value must be less than {error['limit_value']}"
            suggestions["example"] = f"{float(error['limit_value']) - 1}"

    elif "enum" in error_type:
        if "permitted" in error:
            allowed_values = ", ".join([f'"{val}"' for val in error["permitted"]])
            suggestions["fix"] = f"Value must be one of: {allowed_values}"

    elif "json" in error_type:
        suggestions["fix"] = "Provide valid JSON format"

    elif "uuid" in error_type:
        suggestions["fix"] = "Provide a valid UUID (e.g., 123e4567-e89b-12d3-a456-426614174000)"

    elif "datetime" in error_type:
        suggestions["fix"] = "Provide a valid ISO 8601 datetime (e.g., 2023-01-01T12:00:00Z)"

    elif "url" in error_type:
        suggestions["fix"] = "Provide a valid URL (e.g., https://example.com)"

    elif "email" in error_type:
        suggestions["fix"] = "Provide a valid email address"

    return suggestions


def register_exceptions(app: FastAPI) -> None:
    """
    Registers custom exception handlers for the FastAPI application.

    Parameters:
    - app (FastAPI): The FastAPI application instance to register the exception handlers for.
    """
    app.add_exception_handler(
        RequestValidationError,
        make_exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY),
    )
    # app.add_exception_handler(
    #     QueryException,
    #     make_exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
    # )


# TODO: Auth logic should be moved into global middleware _per router_
#       Because some routes don't require auth
# See: https://fastapi.tiangolo.com/tutorial/bigger-applications/
#

# Add other routers with the get_api_key dependency
if enable_responses:
    app.include_router(responses.router, dependencies=[Depends(get_api_key)])
else:
    app.include_router(agents.router, dependencies=[Depends(get_api_key)])
    app.include_router(sessions.router, dependencies=[Depends(get_api_key)])
    app.include_router(users.router, dependencies=[Depends(get_api_key)])
    app.include_router(files.router, dependencies=[Depends(get_api_key)])
    app.include_router(docs.router, dependencies=[Depends(get_api_key)])
    app.include_router(tasks.router, dependencies=[Depends(get_api_key)])
    app.include_router(internal.router)
app.include_router(jobs.router, dependencies=[Depends(get_api_key)])
app.include_router(healthz.router)
# TODO: CORS should be enabled only for JWT auth
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# TODO: GZipMiddleware should be enabled only for non-streaming routes
# app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=3)

register_exceptions(app)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):  # pylint: disable=unused-argument
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": str(exc.detail),
                "code": getattr(exc, "code", f"http_{exc.status_code}"),
                "type": "http_error",
            }
        },
    )


@app.exception_handler(RPCError)
async def validation_error_handler(request: Request, exc: RPCError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "message": "job not found or invalid",
                "code": exc.status.name,
                "type": "rpc_error",
            }
        },
    )


@app.exception_handler(BaseCommonException)
async def session_not_found_error_handler(request: Request, exc: BaseCommonException):
    return JSONResponse(
        status_code=exc.http_code,
        content={
            "error": {
                "message": str(exc),
                "code": getattr(exc, "code", "common_error"),
                "type": exc.__class__.__name__,
            }
        },
    )


@app.exception_handler(PromptTooBigError)
async def prompt_too_big_error(request: Request, exc: PromptTooBigError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "message": str(exc),
                "code": "prompt_too_big",
                "type": "PromptTooBigError",
                "fix": "Reduce the size of your prompt or use a model with a larger context window",
            }
        },
    )


@app.exception_handler(APIError)
async def litellm_api_error(request: Request, exc: APIError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": {
                "message": str(exc),
                "code": "llm_api_error",
                "type": "LLMServiceError",
                "fix": "Please check your API keys and model configurations or try again later",
            }
        },
    )


def main(
    host="127.0.0.1",
    port=8000,
    backlog=4096,
    timeout_keep_alive=30,
    workers=None,
    log_level="info",
) -> None:
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        timeout_keep_alive=timeout_keep_alive,
        backlog=backlog,
        workers=workers,
    )


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
