# Routers

## Purpose
- Define FastAPI route handlers for HTTP endpoints
- Organized by resource types (agents, tasks, sessions, etc.)
- Handle authentication, validation, and error handling

## Key Routers

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

### users/ and files/
- User management and authentication
- File upload, download, and management

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