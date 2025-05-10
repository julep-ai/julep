# CLAUDE.md - worker

This folder contains the Temporal worker setup for processing agents-api workflows and activities.

Key Points
- Entrypoint script: `run_worker.py` initializes the Temporal worker.
- Register both workflows and activities in worker setup.
- Configure `TEMPORAL_URL` and retry policies via environment variables.
- Logging and monitoring configured in `logging.yaml`.
- Use `poe test` for basic worker smoke tests.

## Purpose
- Temporal worker process for executing workflows and activities
- Handles background processing of tasks
- Entry point for the worker service

## Key Components

### worker.py
- Configures and registers Temporal worker
- Registers workflows and activities
- Sets limits on concurrency and throughput

### codec.py
- Custom codec for Temporal payload processing
- Handles serialization/deserialization
- Supports large object handling with S3 storage

### __main__.py
- Entry point for worker service
- Connects to Temporal service
- Starts worker processes

## Worker Configuration
- Task queue: Configured to listen on specific queue
- Concurrency limits:
  - Maximum concurrent workflow tasks
  - Maximum concurrent activities
  - Rate limits for activities per second
- Graceful shutdown with timeout

## Registered Components
- Workflows: TaskExecutionWorkflow, DemoWorkflow
- Activities: All task_steps, execute_api_call, execute_system, etc.

## Remote Object Handling
- Large objects stored in S3 via RemoteObject
- Automatic serialization/deserialization
- Prevents Temporal payload size limitations