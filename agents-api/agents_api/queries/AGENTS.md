# AGENTS.md - queries

This folder contains database query builders and SQL files for `agents-api`.

Key Points
- Organize queries by domain under subfolders (agents, chat, tasks, etc.).
- Use asyncpg for execution and return typed Pydantic models.
- Validate SQL syntax with `poe check`.
- Add new queries in `queries/` and index them if needed.
- Tests reside under `agents-api/tests/`.
- Add `AIDEV-NOTE` anchors at the top of query modules to clarify module purpose.

# Queries

## Purpose
- Database access layer for the application
- SQL query execution and result processing
- Organized by resource types matching API endpoints

## Key Query Modules

### projects/
- Create, list, and check for project existence
- Project association with resources

### agents/, tasks/, sessions/, users/
- CRUD operations for core resources
- Data validation and normalization
- Project association handling

### secrets/
- Secure storage and retrieval of sensitive data
- Key-value storage with encryption
- Access control and validation

### usage/
- Usage tracking and cost calculation
- User activity monitoring
- Billing and analytics data

### executions/
- Create and track task executions
- Handle execution transitions
- Map between Temporal workflows and API data

### docs/
- Document storage and retrieval
- Text search (search_docs_by_text)
- Embedding search (search_docs_by_embedding)
- Hybrid search combining both approaches

### entries/
- Record chat history and interactions
- Retrieve conversation history

## Common Patterns
- Async functions for database operations
- Connection pool management
- Data serialization/deserialization
- Pydantic model integration

## Usage Pattern
1. Query function receives parameters and optional connection_pool
2. SQL query construction (often with query parameters)
3. Execute query via asyncpg
4. Process results into Pydantic models
5. Return typed response

## Important Functions
- `prepare_execution_input`: Builds inputs for Temporal workflows
- `create_execution_transition`: Records state changes in executions
- `search_docs_hybrid`: Combined embedding and text search
