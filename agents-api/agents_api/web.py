"""
This module initializes the FastAPI application, registers routes, sets up middleware, and configures exception handlers.
"""

import logging

import fire
import sentry_sdk
import uvicorn
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from litellm.exceptions import APIError
from pycozo.client import QueryException
from temporalio.service import RPCError

from agents_api.common.exceptions import BaseCommonException
from agents_api.dependencies.auth import get_api_key
from agents_api.env import sentry_dsn
from agents_api.exceptions import PromptTooBigError
from agents_api.routers import (
    agents,
    tasks,
)

if not sentry_dsn:
    print("Sentry DSN not found. Sentry will not be enabled.")
else:
    sentry_sdk.init(
        dsn=sentry_dsn,
        enable_tracing=True,
    )


logger = logging.getLogger(__name__)


def make_exception_handler(status: int):
    """
    Creates a custom exception handler for the application.

    Parameters:
    - status (int): The HTTP status code to return for this exception.

    Returns:
    A callable exception handler that logs the exception and returns a JSON response with the specified status code.
    """

    async def _handler(request: Request, exc):
        exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
        logger.exception(exc)
        content = {"status_code": status, "message": exc_str, "data": None}
        return JSONResponse(content=content, status_code=status)

    return _handler


def register_exceptions(app: FastAPI):
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


app = FastAPI(dependencies=[Depends(get_api_key)])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

register_exceptions(app)

app.include_router(agents.router)
# app.include_router(sessions.router)
# app.include_router(users.router)
# app.include_router(jobs.router)
app.include_router(tasks.router)


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
):
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        timeout_keep_alive=timeout_keep_alive,
        backlog=backlog,
        workers=workers,
    )


# Check if the script is being run directly and, if so, start the Uvicorn server with the specified configuration.
if __name__ == "__main__":
    fire.Fire(main)
