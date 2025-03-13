"""Web server for the Responses API."""

import logging
import time
from typing import Callable

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration

from responses_api.env import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configure Sentry if DSN is provided
if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        environment=config.ENV,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
    )

# Create FastAPI app
app = FastAPI(
    title="Responses API",
    description="OpenAI Responses API implementation for Julep",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """Log all requests with timing information."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s"
    )
    return response

# Add Prometheus metrics if enabled
if config.ENABLE_METRICS:
    Instrumentator().instrument(app).expose(app)

# Import and include routers
from responses_api.routers import responses

app.include_router(responses.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Responses API",
        "version": "1.0.0",
        "description": "OpenAI Responses API implementation for Julep",
    } 