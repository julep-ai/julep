# Julep Development Guidelines

## Build & Test Commands
- **Format code**: `poe format` (runs `ruff format`)
- **Lint code**: `poe lint` (runs `ruff check`)
- **Type checking**: `poe typecheck` (runs `pytype --config pytype.toml` or `pyright` for CLI)
- **Test**: `poe test` (runs `ward test --exclude .venv` or `pytest` for integrations-service)
- **Single test**: `poe test --search "pattern"` (e.g., `poe test --search "test_session_routes"`)
- **Quick test file**: `PYTHONPATH=$PWD python tests/test_file.py` (for simple tests)
- **Run all checks**: `poe check` (runs lint, format, typecheck, SQL validation)
- **Generate API code**: `poe codegen`

Note: Always prefer using `poe` commands over direct tool invocation when available. The project uses poethepoet (poe) as a task runner to ensure consistent environment and configuration.

## Code Style
- **Python**: 3.12+ (fastAPI, async/await preferred)
- **Line length**: 96 characters
- **Indentation**: 4 spaces
- **Quotes**: Double quotes
- **Imports**: Use ruff's import organization (isort compatible)
- **Types**: Use strict typing (Pydantic models preferred)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Use typed exceptions, context managers for resources
- **Documentation**: Docstrings for public functions/classes
- **Testing**: Separate test files matching source file patterns

## Project Structure
See `CONTRIBUTING.md` for details on architecture and component relationships.

## Core System Components
- **agents-api**: Main service implementing agent and task functionality
- **memory-store**: PostgreSQL database with TimescaleDB for persistent storage
- **blob-store**: Object storage for files and binary data
- **scheduler**: Temporal workflow engine for execution orchestration  
- **integrations-service**: External service integrations (browsers, APIs, etc.)
- **gateway**: API gateway for routing and request handling
- **llm-proxy**: LLM service proxy using litellm
- **monitoring**: Monitoring infrastructure with Prometheus and Grafana
- **typespec**: API specifications in TypeSpec format
- **sdks**: Client SDKs for Node.js and Python

## Directory-Specific Documentation
When working in specific directories, check for CLAUDE.md files that contain detailed notes on architecture, patterns, and implementation details. These files are designed to be LLM-friendly and provide context for making changes.

- **agents-api/CLAUDE.md**: Service-level overview for Agents API
- **agents-api/agents_api/activities/CLAUDE.md**: Temporal activities for task execution
- **agents-api/agents_api/autogen/CLAUDE.md**: Auto-generated TypeSpec API models
- **agents-api/agents_api/clients/CLAUDE.md**: External service client implementations
- **agents-api/agents_api/common/CLAUDE.md**: Shared utilities and protocol definitions
- **agents-api/agents_api/queries/CLAUDE.md**: Database query implementations
- **agents-api/agents_api/routers/CLAUDE.md**: API endpoint handlers
- **agents-api/agents_api/worker/CLAUDE.md**: Temporal worker configuration
- **agents-api/agents_api/workflows/CLAUDE.md**: Workflow definitions and helpers
- **memory-store/CLAUDE.md**: Database schemas and data storage architecture
- **integrations-service/CLAUDE.md**: External integrations architecture and patterns
- **cli/CLAUDE.md**: CLI architecture, workflows, and command structure
- **typespec/CLAUDE.md**: API specifications and TypeSpec architecture

Always refer to these files first when analyzing code or making changes in the corresponding directories to ensure consistency with architectural patterns and implementation details.

## Important Developer Notes

### Working with Python expressions in tasks
- Python expressions in tasks are evaluated using `simpleeval` in a sandbox environment
- Use `validate_py_expression()` from `base_evaluate.py` to statically check expressions
- Expression validation checks syntax, undefined names, unsafe operations, and runtime errors
- All expressions should have access to `_` (current input) and stdlib modules 
- Testing expressions: `PYTHONPATH=$PWD python -c "from agents_api.activities.task_steps.base_evaluate import validate_py_expression; print(validate_py_expression('$ your_expr_here'))"` 
- Task validation handles both raw task dictionaries and Pydantic models (after task_to_spec conversion)
- When a task is converted through task_to_spec, step types can change (e.g., "if" becomes "if_else" with alias)
- The `validate_task_expressions` function needs to check for both `kind_` field (in converted tasks) and for step type keys (in raw tasks)
- For "if_else" steps, the condition is in the `if_` field (with alias "if") to avoid Python keyword conflicts

### Ward Testing Framework 
- Use descriptive Ward test names: `@test("What the test is verifying")`
- When testing specific patterns: `poe test --search "pattern_to_match"` (NOT `-p` which isn't supported in Ward)
- Limit failures for faster feedback: `poe test --fail-limit 1 --search "pattern_to_match"`
- For quick Python script tests, use `PYTHONPATH=$PWD python tests/test_file.py`
- The environment needs to be activated: `source .venv/bin/activate`
- Path issues: Make sure you're in the right directory (agents-api/, not julep/)

### Common Mistakes to Avoid
- Mixing pytest and ward syntax: Ward uses `@test()` decorator, not pytest fixtures/classes
- Forgetting to activate venv: Always run `source .venv/bin/activate` first
- PYTHONPATH issues: Use `PYTHONPATH=$PWD` for script-based tests
- Running from wrong directory: Make sure to cd into agents-api/ not the parent julep/
- Insufficient error inspection: Use simple script-based tests to isolate validation issues