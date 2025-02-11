import os
from contextlib import asynccontextmanager
from typing import Protocol

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from aiobotocore.client import AioBaseClient
    from aiobotocore.session import get_session
    from asyncpg.pool import Pool
    from fastapi import APIRouter, FastAPI
    from prometheus_fastapi_instrumentator import Instrumentator
    from scalar_fastapi import get_scalar_api_reference

    from .clients.pg import create_db_pool
    from .env import api_prefix, hostname, pool_max_size, protocol, public_port


class State(Protocol):
    postgres_pool: Pool | None
    s3_client: AioBaseClient | None


class ObjectWithState(Protocol):
    state: State


# TODO: This currently doesn't use env.py, we should move to using them
@asynccontextmanager
async def lifespan(container: FastAPI | ObjectWithState):
    # INIT POSTGRES #
    pg_dsn = os.environ.get("PG_DSN")

    pool = await create_db_pool(pg_dsn, max_size=pool_max_size, min_size=min(pool_max_size, 10))

    if hasattr(container, "state") and not getattr(container.state, "postgres_pool", None):
        container.state.postgres_pool = pool

    # INIT S3 #
    s3_access_key = os.environ.get("S3_ACCESS_KEY")
    s3_secret_key = os.environ.get("S3_SECRET_KEY")
    s3_endpoint = os.environ.get("S3_ENDPOINT")

    if hasattr(container, "state") and not getattr(container.state, "s3_client", None):
        session = get_session()
        container.state.s3_client = await session.create_client(
            "s3",
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint,
        ).__aenter__()

    try:
        yield
    finally:
        # CLOSE POSTGRES #
        if hasattr(container, "state") and getattr(container.state, "postgres_pool", None):
            pool = getattr(container.state, "postgres_pool", None)
            if pool:
                await pool.close()
            container.state.postgres_pool = None

        # CLOSE S3 #
        if hasattr(container, "state") and getattr(container.state, "s3_client", None):
            s3_client = getattr(container.state, "s3_client", None)
            if s3_client:
                await s3_client.close()
            container.state.s3_client = None


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
)

# Enable metrics
Instrumentator(excluded_handlers=["/metrics", "/docs", "/openapi.json"]).instrument(app).expose(
    app, include_in_schema=False
)

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


# TODO: Implement correct content-length validation (using streaming and chunked transfer encoding)
# NOTE: This relies on client reporting the correct content-length header
# @app.middleware("http")
# async def validate_content_length(
#     request: Request,
#     call_next: Callable[[Request], Coroutine[Any, Any, Response]],
# ):
#     content_length = request.headers.get("content-length")

#     if not content_length:
#         return Response(status_code=411, content="Content-Length header is required")

#     if int(content_length) > max_payload_size:
#         return Response(status_code=413, content="Payload too large")

#     return await call_next(request)
