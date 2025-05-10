# CLAUDE.md - clients

This folder contains API client wrappers for external services used by `agents-api`.

Key Points
- Implement async HTTP clients using `httpx`.
- Obtain and refresh auth tokens via `common/utils/auth.py`.
- Handle HTTP errors with typed exceptions from `common/exceptions`.
- Write unit tests under `agents-api/tests/`.
- Configure endpoints and credentials via environment variables.

# Clients

## Purpose
- Client libraries for external services
- Abstractions for database, storage, and API integrations
- Shared connection management

## Key Clients

### pg.py
- PostgreSQL client using asyncpg
- Connection pool management
- Query execution utilities

### temporal.py
- Temporal workflow service client
- Workflow execution functions
- Job management and tracking

### litellm.py
- LLM provider client abstraction
- Supports multiple models and providers
- Handles completion requests and streaming

### async_s3.py and sync_s3.py
- S3 storage client for object storage
- Used for storing large payloads
- Supports both sync and async patterns

### integrations.py
- Client for integrations service
- Executes integration tools

## Usage Patterns
- Clients initialized during application startup
- Connection pooling for efficiency
- Error handling and retry logic
- Async-first approach with proper cleanup