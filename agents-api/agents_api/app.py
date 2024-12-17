import json
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .clients.pg import create_db_pool
from .env import api_prefix


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.postgres_pool = await create_db_pool()
    yield
    await app.state.postgres_pool.close()


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
    lifespan=lifespan,
)

# Enable metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)
