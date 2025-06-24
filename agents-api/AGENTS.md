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
  - Tests live under `agents-api/tests/` using `pytest`.
  - Run specific tests: `poe test -k "pattern" -x`.
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

## Testing Framework
- AIDEV-NOTE: Successfully migrated from Ward to pytest (2025-06-24)
- All test files now use pytest conventions (test_* functions)
- Fixtures centralized in conftest.py with pytest_asyncio for async tests
- S3 client fixture fixed for async event loop compatibility using AsyncExitStack
- Usage cost tests updated to use dynamic pricing from litellm
- All Ward imports removed, migration complete
- Run tests: `poe test` or `poe test -k "pattern"` for specific tests
- Stop on first failure: `poe test -x`

## Type Checking
- AIDEV-NOTE: autogen/openapi_model.py is handwritten, not auto-generated
- Type checking errors from openapi_model.py are intentional (dynamic type property patches)
- Use `ty check` for extremely fast type checking (pytype replacement)
