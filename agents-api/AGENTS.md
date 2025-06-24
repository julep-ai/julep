# AGENTS.md - agents-api

This directory hosts the `agents-api` FastAPI service and Temporal workflows for agent definitions and task execution.

Key Uses
- Bash commands:
  - cd agents-api
  - source .venv/bin/activate
  - poe format
  - poe lint
  - poe typecheck
  - ty check [PATH]…           # Extremely fast Python type checker (default: project root)
  - ty server                  # Start the ty language server for editor integration
  - ty version                 # Display ty's version
  - poe test
  - poe check
  - bash scripts/generate_openapi_code.sh
- Core files and utilities:
  - `agents_api/` contains routers, activities, workflows.
  - `agents_api/common/` for exceptions, protocol, and utils.
- Code style guidelines:
  - Follows root `AGENTS.md` Python standards (FastAPI, async/await, ruff formatting).
- Testing instructions:
  - Tests live under `agents-api/tests/` using `ward`.
  - Run specific tests: `poe test --search "pattern" --fail-limit 1`.
- Repository etiquette:
  - Tag AI-generated commits with `[AI]`.
- Developer environment:
  - Ensure `PYTHONPATH=$PWD` and correct CWD in `agents-api/`.
- Unexpected behaviors:
  - Remember to regenerate autogen code after TypeSpec changes.

# Julep Agents API

## Service Overview
- FastAPI-based service for orchestrating agent workflows 
- Handles tasks, executions, sessions, and tools
- Temporal-based workflow engine for task execution
- PostgreSQL for data storage
- S3 for remote object storage

## Architecture
- REST API (defined in routers/)
- Database queries (queries/)
- Workflow definitions (workflows/)
- Task activities (activities/)
- Background worker processing (worker/)
- Common utilities and protocol definitions (common/)
- Dependencies for authentication and middleware (dependencies/)
- Recursive summarization for message history (rec_sum/)
- Metrics collection and monitoring (metrics/)

## Key Concepts
- Projects: Organizational units for grouping related resources
- Tasks: Workflow specifications with steps and tools
- Executions: Running instances of tasks
- Sessions: User interaction contexts
- Agents: LLM-based interfaces for users
- Tools: Integrations and capabilities usable by agents

## Runtime Flow
- User defines tasks with step definitions
- Task execution creates workflow in Temporal
- Activities run individual steps (prompt, tool calls, etc.)
- Transitions track execution state
- Results stored in database, retrievable via API

## Expression Evaluation
- Task steps use Python expressions for logic/data flow
- Expressions prefixed with '$' executed in sandbox
- Backward compatibility: '{{variable}}' → '${variable}'
- Input context: '_' holds current input, 'inputs' and 'outputs' for history

## Validation
- Expression validation checks syntax, undefined names, unsafe operations
- Task validation checks all expressions in workflow steps
- Security: Sandbox with limited function/module access

## SQL Safety Requirements
- ALWAYS use the SQL utilities from `agents_api/queries/sql_utils.py`
- NEVER use string formatting (f-strings, .format(), %) for SQL queries
- Use `SafeQueryBuilder` for complex queries with dynamic WHERE, ORDER BY, LIMIT
- Use `safe_format_query` for simple ORDER BY validation
- All sort fields must be whitelisted explicitly
- Run SQL injection tests: `poe test --search "sql_injection_prevention"`

### Example Usage
```python
# For complex queries
from agents_api.queries.sql_utils import SafeQueryBuilder

builder = SafeQueryBuilder("SELECT * FROM docs WHERE developer_id = $1", [dev_id])
if metadata_filter:
    for key, value in metadata_filter.items():
        builder.add_condition(" AND metadata->>{}::text = {}", key, str(value))
builder.add_order_by("created_at", "desc", allowed_fields={"created_at", "updated_at"})
builder.add_limit_offset(limit, offset)
query, params = builder.build()

# For simple ORDER BY queries
from agents_api.queries.sql_utils import safe_format_query

query = safe_format_query(
    "SELECT * FROM entries ORDER BY {sort_by} {direction}",
    sort_by="created_at",
    direction="desc",
    allowed_sort_fields={"created_at", "timestamp"}
)
```
