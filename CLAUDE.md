# CLAUDE.md - Julep AI Codebase Reference

## Build/Lint/Test Commands
- Python lint: `poe lint` or `ruff check`
- Python format: `poe format` or `ruff format`
- Python typecheck: `poe typecheck` or `pytype --config pytype.toml`
- Python test: `poe test` or use `pytest tests/test_file.py::test_function`
- SQL validation: `poe validate-sql`
- Full check: `poe check` (lint + format + validate-sql + typecheck)
- Node build: `yarn build` or `./scripts/build`
- Node test: `yarn test` or `./scripts/test`
- Node lint: `yarn lint` or `./scripts/lint`
- Node format: `yarn format` or `./scripts/format`

## Code Style Guidelines
- Python: Use snake_case for variables/functions, PascalCase for classes
- Python: Strict typing with annotations; use pydantic for data validation
- Python: Max line length 96 characters, 4 spaces indentation
- TypeScript: camelCase for variables/functions, PascalCase for classes
- Import order: standard library, third-party, local packages
- Define custom exceptions in dedicated exceptions.py modules
- Use async/await patterns consistently where applicable
- Follow microservice architecture patterns within Docker Compose
- Add docstrings to functions/classes for better documentation