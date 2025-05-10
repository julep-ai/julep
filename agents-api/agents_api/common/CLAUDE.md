# CLAUDE.md - common

This folder contains shared utilities, protocol definitions, and exceptions for `agents-api`.

Key Points
- Exceptions defined in `exceptions/`; always use typed exception classes.
- Pydantic models in `protocol/` for request/response schemas.
- Utilities in `utils/` leverage context managers for resource handling.
- Use `AIDEV-NOTE:` anchors in complex utilities to aid future AI/developer context.
- Follow root coding standards for formatting and naming.

## Purpose
- Shared utilities, protocols, and type definitions
- Cross-cutting concerns like error handling
- Data models and protocols for system communication

## Key Components

### protocol/
- Data models for inter-component communication
- `models.py`: Core data transformations (task_to_spec, spec_to_task)
- `tasks.py`: Task execution state machine and transition logic
- `state_machine.py`: Definition of valid state transitions

### utils/
- `task_validation.py`: Validates Python expressions in tasks
- `workflows.py`: Helper functions for workflow handling
- `messages.py`: Message processing utilities
- `mmr.py`: Maximum Marginal Relevance for document search

### exceptions/
- Typed exceptions for different resource types
- HTTP-friendly error structures with status codes

## Important Functions
- `task_to_spec`: Converts API task model to execution spec
  - Handles workflow steps, tools, and configuration
  - Crucial transformation for task execution
  - Converts step types (e.g., "if" → "if_else" with alias)
  
- `validate_py_expression`: Static validation for expressions
  - Checks syntax, undefined names, unsafe operations
  - Used before task execution to catch errors early

## State Machine
- Defined in `tasks.py` with valid transition mappings
- Execution progresses through states: queued → starting → running → succeeded/failed
- Transitions trigger API state updates and execution logging