# Autogen

## Purpose
- Auto-generated API client code from OpenAPI specifications
- Provides type-safe models for API resources
- Generated from TypeSpec definitions (in typespec/ directory)

## Key Components

### openapi_model.py
- Pydantic models for all API resources
- Request/response schemas
- Type definitions and validations

### Resource Models
- `Agents.py`: Agent definitions and configurations
- `Tasks.py`: Task specifications and step definitions
- `Executions.py`: Execution tracking and state
- `Sessions.py`: Chat session management
- `Tools.py`: Tool definitions and schemas

### Shared Models
- `Common.py`: Shared types and utilities

## Model Hierarchy
- Base models define common fields (id, created_at, etc.)
- Request models for API inputs
- Response models for API outputs
- Specialized models for different step types (evaluate, tool, prompt, etc.)

## Usage Pattern
1. Import from autogen.openapi_model
2. Use models for request/response validation
3. Models automatically handle serialization/deserialization

## Important Models
- `TaskSpecDef`: Complete task specification for execution
- `WorkflowStep`: Individual step in a workflow
- `ApiCallDef`, `PromptDef`: Tool type definitions
- `ExecutionStatus`: State machine status values