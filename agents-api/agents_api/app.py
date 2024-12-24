import os
from contextlib import asynccontextmanager
from typing import Any, Callable, Coroutine

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.params import Depends
from prometheus_fastapi_instrumentator import Instrumentator
from scalar_fastapi import get_scalar_api_reference

from .clients.pg import create_db_pool
from .dependencies.content_length import valid_content_length
from .env import api_prefix, hostname, max_payload_size, protocol, public_port


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_dsn = os.environ.get("DB_DSN")

    if not getattr(app.state, "postgres_pool", None):
        app.state.postgres_pool = await create_db_pool(db_dsn)

    yield

    if getattr(app.state, "postgres_pool", None):
        await app.state.postgres_pool.close()
        app.state.postgres_pool = None


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
        "email": "developers@julep.ai",
    },
    root_path=api_prefix,
    lifespan=lifespan,
    #
    # Global dependencies
    dependencies=[Depends(valid_content_length)],
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


# content-length validation
# NOTE: This relies on client reporting the correct content-length header
# TODO: We should use streaming for large payloads
@app.middleware("http")
async def validate_content_length(
    request: Request,
    call_next: Callable[[Request], Coroutine[Any, Any, Response]],
):
    content_length = request.headers.get("content-length")

    if not content_length:
        return Response(status_code=411, content="Content-Length header is required")

    if int(content_length) > max_payload_size:
        return Response(status_code=413, content="Payload too large")

    return await call_next(request)
