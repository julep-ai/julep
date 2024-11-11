"""
This module initializes the FastAPI application, registers routes, sets up middleware, and configures exception handlers.
"""

import asyncio
import logging
from typing import Any, Callable, Union, cast

import sentry_sdk
import uvicorn
import uvloop
from fastapi import APIRouter, Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from litellm.exceptions import APIError
from prometheus_fastapi_instrumentator import Instrumentator
from pycozo.client import QueryException
from pydantic import ValidationError
from scalar_fastapi import get_scalar_api_reference
from temporalio.service import RPCError

from .common.exceptions import BaseCommonException
from .dependencies.auth import get_api_key
from .env import api_prefix, hostname, protocol, public_port, sentry_dsn
from .exceptions import PromptTooBigError
from .routers import (
    agents,
    docs,
    internal,
    jobs,
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
        location = None
        offending_input = None

        # Return the deepest matching possibility
        if isinstance(exc, (ValidationError, RequestValidationError)):
            exc = cast(Union[ValidationError, RequestValidationError], exc)
            errors = exc.errors()

            # Get the deepest matching errors
            max_depth = max(len(error["loc"]) for error in errors)
            errors = [error for error in errors if len(error["loc"]) == max_depth]

            # Get the common location
            location = errors[0]["loc"]
            for error in errors[1:]:
                for a, b in zip(location, error["loc"]):
                    if a == b:
                        continue
                    location = location[:-1]
                    break

            location = location[1:]  # Skip the first element ("body")

            # Get the part of the input that caused the error
            offending_input = exc.body
            for loc in location:
                match offending_input:
                    case dict():
                        if loc not in offending_input:
                            break
                    case list():
                        if not (
                            isinstance(loc, int) and 0 <= loc < len(offending_input)
                        ):
                            break
                    case _:
                        break

                offending_input = offending_input[loc]

                # Keep only the message from the error
                errors = [
                    error.get("msg", error)
                    if isinstance(error, dict)
                    else getattr(error, "msg", error)
                    for error in errors
                ]

            else:
                errors = exc.errors() if hasattr(exc, "errors") else [exc]

        return JSONResponse(
            content={
                "errors": errors,
                "offending_input": offending_input,
                "location": location,
            },
            status_code=status_code,
        )

    return _handler


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
    app.add_exception_handler(
        QueryException,
        make_exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
    )


# TODO: Auth logic should be moved into global middleware _per router_
#       Because some routes don't require auth
# See: https://fastapi.tiangolo.com/tutorial/bigger-applications/
#
app: FastAPI = FastAPI(
    docs_url="/swagger",
    openapi_prefix=api_prefix,
    redoc_url=None,
    title="Julep Agents API",
    description="API for Julep Agents",
    version="0.4.0",
    terms_of_service="https://www.julep.ai/terms",
    contact={
        "name": "Julep",
        "url": "https://www.julep.ai",
        "email": "team@julep.ai",
    },
    root_path=api_prefix,
)

# Enable metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)

# Create a new router for the docs
scalar_router = APIRouter()


@scalar_router.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url[1:],  # Remove leading '/'
        title=app.title,
        servers=[{"url": f"{protocol}://{hostname}:{public_port}{api_prefix}"}],
    )


# Add the docs_router without dependencies
app.include_router(scalar_router)

# Add other routers with the get_api_key dependency
app.include_router(agents.router, dependencies=[Depends(get_api_key)])
app.include_router(sessions.router, dependencies=[Depends(get_api_key)])
app.include_router(users.router, dependencies=[Depends(get_api_key)])
app.include_router(jobs.router, dependencies=[Depends(get_api_key)])
app.include_router(docs.router, dependencies=[Depends(get_api_key)])
app.include_router(tasks.router, dependencies=[Depends(get_api_key)])
app.include_router(internal.router)

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
        content={"error": {"message": str(exc)}},
    )


@app.exception_handler(RPCError)
async def validation_error_handler(request: Request, exc: RPCError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {"message": "job not found or invalid", "code": exc.status.name}
        },
    )


@app.exception_handler(BaseCommonException)
async def session_not_found_error_handler(request: Request, exc: BaseCommonException):
    return JSONResponse(
        status_code=exc.http_code,
        content={"error": {"message": str(exc)}},
    )


@app.exception_handler(PromptTooBigError)
async def prompt_too_big_error(request: Request, exc: PromptTooBigError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"message": str(exc)}},
    )


@app.exception_handler(APIError)
async def litellm_api_error(request: Request, exc: APIError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"error": {"message": str(exc)}},
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
