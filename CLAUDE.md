# Julep Development Guidelines

## Build & Test Commands
- **Format code**: `ruff format`
- **Lint code**: `ruff check`
- **Type checking**: `pytype --config pytype.toml` (or `pyright` for CLI)
- **Test**: `ward test --exclude .venv` (or `pytest` for integrations-service)
- **Single test**: `ward test -p "pattern"` (e.g., `ward test -p "test_session_routes"`)
- **Quick test file**: `PYTHONPATH=$PWD python tests/test_file.py` (for simple tests)
- **Run all checks**: `poe check` (runs lint, format, typecheck, SQL validation)
- **Generate API code**: `poe codegen`

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

## Important Developer Notes

### Working with Python expressions in tasks
- Python expressions in tasks are evaluated using `simpleeval` in a sandbox environment
- Use `validate_py_expression()` from `base_evaluate.py` to statically check expressions
- Expression validation checks syntax, undefined names, unsafe operations, and runtime errors
- All expressions should have access to `_` (current input) and stdlib modules 
- Testing expressions: `PYTHONPATH=$PWD python -c "from agents_api.activities.task_steps.base_evaluate import validate_py_expression; print(validate_py_expression('$ your_expr_here'))"` 

### Ward Testing Framework 
- Use descriptive Ward test names: `@test("What the test is verifying")`
- When testing specific patterns: `ward test -p "pattern_to_match"` 
- For quick Python script tests, use `PYTHONPATH=$PWD python tests/test_file.py`
- The environment needs to be activated: `source .venv/bin/activate`
- Path issues: Make sure you're in the right directory (agents-api/, not julep/)

### Common Mistakes to Avoid
- Mixing pytest and ward syntax: Ward uses `@test()` decorator, not pytest fixtures/classes
- Forgetting to activate venv: Always run `source .venv/bin/activate` first
- PYTHONPATH issues: Use `PYTHONPATH=$PWD` for script-based tests
- Running from wrong directory: Make sure to cd into agents-api/ not the parent julep/
- Insufficient error inspection: Use simple script-based tests to isolate validation issues