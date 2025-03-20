# Workflows

## Purpose
- Temporal workflow definitions
- Orchestrate activities in durable, fault-tolerant execution
- Manage execution state and transitions

## Key Workflows

### task_execution/
- `TaskExecutionWorkflow`: Primary workflow for executing tasks
- Executes steps in sequence based on task definition
- Handles workflow transitions, branching, and loops
- Controls execution state machine

### task_execution/helpers.py
- Control flow for workflow execution:
  - `execute_switch_branch`: Handles switch/case logic
  - `execute_if_else_branch`: Conditional execution
  - `execute_foreach_step`: Iteration over collections
  - `execute_map_reduce_step`: Map/reduce operations
  - `execute_map_reduce_step_parallel`: Parallelized map/reduce

## Workflow Execution Model
1. Workflow receives ExecutionInput with task definition
2. For each step in workflow:
   - Determine step type (evaluate, tool, prompt, etc.)
   - Execute corresponding activity
   - Handle result and determine next transition
3. State persists across failures and retries
4. Child workflows used for branching logic

## State Machine
- `init` → `wait`/`error`/`step`/`cancelled`/`init_branch`/`finish`
- Transitions tracked in database
- Status reflected in API responses

## Concurrency and Control
- Parallel execution for map/reduce operations
- Heartbeats for long-running activities
- Workflow continues even if activities fail (with retry policies)