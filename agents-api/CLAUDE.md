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