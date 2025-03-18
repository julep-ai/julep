# Activities

## Purpose
- Houses Temporal activities (atomic units of work) for task execution
- Each activity represents an operation that can be performed within workflows
- Activities have built-in retry policies, timeouts, and heartbeats

## Key Activities

### task_steps/
- `base_evaluate`: Evaluates Python expressions in a sandbox environment (simpleeval)
- `get_value_step`: Retrieves values from context
- `pg_query_step`: Executes PostgreSQL queries
- `prompt_step`: Generates text using LLMs
- `tool_call_step`: Calls tools (integrations with external systems)
- `transition_step`: Handles workflow transitions

### External Operations
- `execute_api_call`: Makes HTTP requests to external APIs
- `execute_integration`: Calls integrations service
- `execute_system`: Performs system operations

### Data Management
- `sync_items_remote`: Saves/loads large objects to/from S3

## Expression Handling
- Python expressions prefixed with `$` parsed by base_evaluate
- Backward compatibility for {{var}} template syntax → $f'''{{var}}'''
- Security: Limited functions, modules, operations in sandbox
- Validation: Syntax, undefined names, unsafe operations checked

## Context
- Task steps receive `StepContext` with:
  - Current cursor position (workflow, step, scope)
  - Input data for the step
  - Previous inputs/outputs in the workflow
  - Agent configuration and tools