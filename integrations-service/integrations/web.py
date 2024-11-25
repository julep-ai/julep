import asyncio
import logging
import os
from typing import Any, Callable

import uvicorn
import uvloop
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .routers.execution.router import router as execution_router
from .routers.integrations.router import router as integrations_router

app: FastAPI = FastAPI(
    title="Integrations Service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    default_response_class=JSONResponse,
)

# Add GZIP compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add routers
app.include_router(integrations_router)
app.include_router(execution_router)

# Optimize event loop policy
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Configure logging once at startup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger: logging.Logger = logging.getLogger(__name__)

# Add connection pooling for common clients
from httpx import AsyncClient

http_client = AsyncClient()


@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()


def make_exception_handler(status: int) -> Callable[[Any, Any], Any]:
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


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):  # pylint: disable=unused-argument
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": str(exc)}},
    )


def main(
    host="0.0.0.0",
    port=8000,
    backlog=4096,
    timeout_keep_alive=30,
    workers=None,
    log_level="info",
    reload=bool(os.environ.get("RELOAD")),
) -> None:
    print(f"Reload: {reload}")

    uvicorn.run(
        "integrations.web:app",
        host=host,
        port=port,
        log_level=log_level,
        timeout_keep_alive=timeout_keep_alive,
        backlog=backlog,
        workers=workers,
        reload=reload,
    )
