# AGENTS.md - routers

This folder contains FastAPI route definitions for `agents-api` endpoints.

Key Points
- Follow RESTful CRUD patterns for resource routes.
- Use dependency injection for authentication and authorization.
- Response models sourced from `autogen/` or `protocol/`.
- Document new endpoints in `openapi.yaml` and regenerate clients as needed.
- Run `poe codegen` after TypeSpec updates.
- Place route-specific tests under `agents-api/tests/`.

# Routers

## Purpose
- Define FastAPI route handlers for HTTP endpoints
- Organized by resource types (agents, tasks, sessions, etc.)
- Handle authentication, validation, and error handling

## Key Routers

### projects/
- Project creation and listing
- Resource organization and management

### agents/
- CRUD operations for agents (AI assistants)
- Tool management for agents

### tasks/
- Task definition and management
- Task execution creation and control
- Execution transitions and streaming events

### sessions/
- Chat session management
- Handle chat completions through LLM providers
- Streaming responses for chat messages

### docs/
- Document management (knowledge base)
- Embeddings generation
- Vector and text search capabilities

### users/
- User management and authentication
- User CRUD operations

### files/
- File upload, download, and management
- File metadata and storage

### secrets/
- Secret management for secure storage
- Create, update, delete, and list secrets

### responses/
- Response management for task executions
- Response creation and retrieval

### healthz/
- Health check endpoints
- Service status monitoring

### internal/
- Internal API endpoints
- System-level operations

### jobs/
- Job management and scheduling
- Background task coordination

## Common Patterns
- Most endpoints require developer_id authentication
- Routes follow RESTful conventions
- Streaming endpoints use `StreamingResponse`
- Background tasks for post-request operations

## Request Flow
1. API call hits a router endpoint
2. Authentication/authorization via dependencies
3. Input validation with Pydantic models
4. Query execution against database
5. Optional: workflow triggering for long-running operations
6. Response formatting and return

## Error Handling
- Structured error responses with details and suggestions
- HTTP-appropriate status codes
- Validation errors include field location and fix recommendations
