# Julep Platform FAQ

This comprehensive FAQ document covers all aspects of the Julep platform, from architecture to troubleshooting. The information is organized by category for easy navigation.

## Table of Contents

1. [Architecture & System Design](#architecture--system-design)
2. [Data Model & Storage](#data-model--storage)
3. [Task Execution & Workflow](#task-execution--workflow)
4. [Agents API](#agents-api)
5. [Worker System & Integration](#worker-system--integration)
6. [Development & Deployment](#development--deployment)
7. [Performance & Optimization](#performance--optimization)
8. [Security & Compliance](#security--compliance)
9. [Advanced Use Cases & Patterns](#advanced-use-cases--patterns)
10. [Troubleshooting & Common Issues](#troubleshooting--common-issues)

---

## Architecture & System Design

### Q: What is the overall system architecture of Julep, including all core components and their interactions?

Julep is a distributed system built on a microservices architecture designed to orchestrate complex AI workflows. The main components include:

- **Client Applications**: Initiate requests to the Julep system
- **Gateway**: Entry point for all API requests, handles authentication and load balancing (implemented using Traefik)
- **Agents API**: Provides REST endpoints for managing agents, tasks, sessions, and documents; initiates workflows in Temporal
- **Temporal Workflow Engine**: Orchestrates durable workflow execution, retries, and state management
- **Worker System**: Executes workflows and activities defined in Temporal by polling for tasks
- **LiteLLM Proxy**: Provides a unified interface for interacting with various LLM providers
- **Memory Store**: Provides persistent storage using PostgreSQL/TimescaleDB for relational data and vector embeddings
- **Integration Service**: Enables connections with external tools and APIs

### Q: How does Julep handle distributed task execution and what role does Temporal play in the architecture?

Julep handles distributed task execution primarily through the Temporal Workflow Engine:

- **Workflow Orchestration**: Temporal ensures durable execution of workflows, handling retries and maintaining state across failures
- **Task Queues**: The Agents API initiates workflows by sending requests to Temporal, which places them on task queues like `julep-task-queue`
- **Worker Execution**: Workers poll Temporal for tasks and execute activities like LLM calls, tool operations, and data interactions
- **State Management**: Temporal persists workflow execution state in PostgreSQL, ensuring long-running processes can recover from failures

### Q: What are the key design decisions behind separating agents-api, memory-store, integrations-service, and other components?

The separation follows microservices principles:

- **Modularity and Independent Scaling**: Each service can be developed, deployed, and scaled independently
- **Separation of Concerns**: Each component handles specific functionalities:
  - `agents-api`: Manages agent definitions, tasks, sessions, and orchestrates workflows
  - `memory-store`: Handles all data persistence including relational data and vector embeddings
  - `integrations-service`: Provides standardized interface for external tool usage
  - `llm-proxy`: Centralizes LLM interactions with a unified API
- **Resilience**: Failures in one service are isolated from others
- **Technology Flexibility**: Different services can use different technologies if needed

### Q: How does the gateway component route requests between different services?

The Gateway component uses Traefik and routes requests based on defined rules:

- Requests to `/api/*` are routed to the Agents API service
- Requests to `/tasks-ui/*` go to the Temporal UI service
- `/v1/graphql` requests are directed to the Hasura service
- In multi-tenant setups, it enforces JWT-based authentication and forwards `X-Developer-Id` headers for resource isolation

### Q: What is the role of the blob-store and how does it integrate with S3-compatible storage?

The blob-store is used for persistent storage of large data, specifically for Temporal workflow data when `USE_BLOB_STORE_FOR_TEMPORAL` is enabled. It integrates with S3-compatible storage through environment variables:
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, and `S3_SECRET_KEY` for connection
- `BLOB_STORE_BUCKET` defines the bucket name
- `BLOB_STORE_CUTOFF_KB` sets the size threshold for blob storage

### Q: How does the llm-proxy (LiteLLM) handle different language model providers?

LiteLLM provides a unified interface to multiple LLM providers:
- Supports providers like OpenAI, Anthropic, Gemini, Groq, and OpenRouter
- Configuration defined in `litellm-config.yaml` with model names, parameters, and API keys
- Handles response patching for consistency (e.g., changing `finish_reason` from "eos" to "stop")
- Tracks token usage and costs in PostgreSQL
- Implements request caching using Redis and supports parallel forwarding

### Q: What are the scalability patterns and limitations of the current architecture?

Julep's architecture supports scalability through:
- **Agents API**: Horizontal scaling via multiple instances, configurable with `GUNICORN_WORKERS`
- **Worker**: Multiple workers with concurrency control using `TEMPORAL_MAX_CONCURRENT_ACTIVITIES`
- **Memory Store**: PostgreSQL connection pooling with `POOL_MAX_SIZE`
- **LiteLLM**: Request caching and parallel forwarding
- **Temporal**: Durable workflow execution that scales to handle concurrent tasks

### Q: How does Julep ensure high availability and fault tolerance across services?

High availability is achieved through:
- Temporal's durable execution model with automatic retries
- Microservices architecture allowing independent service failures
- PostgreSQL for persistent state storage
- Worker pools for distributed task execution
- Connection pooling and retry mechanisms

---

## Data Model & Storage

### Q: What is the complete data model including relationships between Agents, Tasks, Tools, Sessions, Entries, and Executions?

The core entities and their relationships:

- **Developer**: Manages Agents, Users, and owns Tasks
- **Agent**: Has Tasks, defines Tools, owns Docs, participates in Sessions
- **User**: Owns Docs and participates in Sessions
- **Task**: Contains WorkflowSteps and is executed as Executions
- **Execution**: Logs Transitions and tracks task execution state
- **Session**: Contains Entries (conversation history)
- **Entry**: Individual messages within a Session
- **Tool**: Capabilities available to Agents
- **Doc**: Documents with embeddings for knowledge base

All entities use UUIDs for identification and include `developer_id` for multi-tenancy.

### Q: How does the memory-store handle vector embeddings and similarity search?

The memory store provides vectorized document storage:
- Documents have an `embeddings` field stored in `docs_embeddings_store` table
- Supports three search types:
  - **Vector Search**: `search_docs_by_embedding` for semantic similarity
  - **Text Search**: `search_docs_by_text` using PostgreSQL full-text search
  - **Hybrid Search**: `search_docs_hybrid` combining both approaches
- Uses cosine similarity for vector comparisons
- Implements Maximum Marginal Relevance (MMR) for result diversity

### Q: What PostgreSQL and TimescaleDB features are leveraged for time-series data?

While PostgreSQL is the primary database, specific TimescaleDB features are not explicitly detailed in the codebase. The system uses:
- Standard PostgreSQL timestamps (`created_at`, `updated_at`) for temporal data
- Time-based filtering in queries (e.g., `list_entries` with date ranges)
- No explicit TimescaleDB-specific features documented

### Q: How are agent instructions and task definitions stored and versioned?

- **Agent Instructions**: Stored as `string` or `array[string]` in the Agent entity
- **Task Definitions**: Stored as Task entities with fields like `name`, `description`, `input_schema`, `main` (workflow steps), and `tools`
- **Versioning**: Handled through UUID changes - altering a UUID creates a new entity while preserving the original
- Timestamps (`created_at`, `updated_at`) provide implicit version tracking

### Q: What is the schema for storing conversation history and context?

Conversation history uses two main entities:
- **Session**: Contains `id`, `user`, `agent`, `situation` (context), `system_template`, and `metadata`
- **Entry**: Contains `id`, `session_id`, `role` (user/assistant/system), `content` (string or JSON), `source`, and `timestamp`
- Sessions group entries and maintain context across conversations

### Q: How does Julep handle data partitioning and archiving for long-running agents?

The codebase does not contain explicit information about data partitioning or archiving strategies. The system uses:
- Multi-tenancy through `developer_id` filtering
- Pagination support for large datasets
- Time-based filtering capabilities
- No documented automatic archiving policies

### Q: What are the indexing strategies for optimizing query performance?

Indexing strategies include:
- Trigram indexes for text search (indicated by `trigram_similarity_threshold` parameter)
- Vector indexes for embedding similarity searches
- Document chunking and embedding storage for efficient retrieval
- Use of prepared statements for query optimization

---

## Task Execution & Workflow

### Q: How does the TaskExecutionWorkflow handle complex multi-step operations?

The TaskExecutionWorkflow orchestrates multi-step operations by:
- Processing different WorkflowStep types through dedicated handlers
- Managing state transitions between steps
- Integrating with Temporal for durability and reliability
- Using `handle_step` method to process each step type
- Evaluating expressions within steps using `eval_step_exprs`

### Q: What are all the possible workflow step types and their configurations?

**Basic Steps:**
- **PromptStep**: Sends prompts to LLMs and handles responses
- **ToolCallStep**: Executes tool calls (functions, integrations, APIs, system operations)
- **EvaluateStep**: Evaluates expressions and returns results
- **SetStep**: Sets values in execution state
- **GetStep**: Retrieves values from execution state
- **LogStep**: Logs messages during execution
- **ReturnStep**: Returns a value and completes workflow
- **ErrorWorkflowStep**: Raises an error and fails the workflow
- **SleepStep**: Pauses execution for specified duration
- **WaitForInputStep**: Pauses for external input

**Control Flow Steps:**
- **IfElseWorkflowStep**: Conditional branching based on condition
- **SwitchStep**: Multi-way branching based on case evaluation
- **ForeachStep**: Iterates over collections
- **MapReduceStep**: Maps function over items with optional parallelism
- **YieldStep**: Yields execution to another workflow
- **ParallelStep**: Executes steps in parallel (not yet implemented)

### Q: How does the state machine handle transitions between different execution states?

The state machine tracks execution through:
- **States**: `queued`, `starting`, `running`, `succeeded`, `failed`, `cancelled`
- **Transitions**: Record state changes with types: `init`, `step`, `finish`, `error`, `cancelled`
- Each transition includes `output`, `current`, and `next` workflow steps
- Transitions stored in `execution_transitions` table
- `create_execution_transition` function records all state changes

### Q: What happens when a task fails midway through execution?

When a task fails:
- Execution status transitions to "failed"
- An "error" transition is created with the error message
- The `error` field of the Execution object is populated
- The system tracks the failure point and error details
- Workflow implements retry policies for retryable errors
- Non-retryable errors cause immediate failure

### Q: How are conditional branches and loops implemented in workflows?

**Conditional Branches:**
- `IfElseWorkflowStep`: Evaluates condition and executes "then" or "else" branch
- `SwitchStep`: Multi-way branching with multiple cases

**Loops:**
- `ForeachStep`: Iterates over collections processing each item
- `MapReduceStep`: Maps functions over collections with optional parallel execution

These are processed by dedicated handlers like `_handle_IfElseWorkflowStep` and `_handle_ForeachStep`.

### Q: What is the retry and error handling strategy for failed steps?

- **Error Classification**: Errors classified as retryable or non-retryable
- **Retry Policy**: `DEFAULT_RETRY_POLICY` applied to retryable errors
- **Max Retries**: Workflow fails if max retries exceeded
- **Error Transitions**: "error" transitions record failure states
- **Last Error Tracking**: `last_error` attribute stores recent errors

### Q: How does Julep handle long-running tasks and prevent timeouts?

Julep uses Temporal's timeout mechanisms:
- `schedule_to_close_timeout` and `heartbeat_timeout` for activities
- Activity and workflow heartbeats ensure progress tracking
- Large data handling via `RemoteObject` pattern to optimize memory
- Blob storage for data exceeding size thresholds

### Q: What are the mechanisms for task cancellation and cleanup?

- **Workflow Cancellation**: Handled through Temporal's cancellation features
- **State Management**: Execution can transition to "cancelled" state
- **Persistence**: All transitions persisted for state restoration
- **Cleanup**: Status updates and transition history provide cleanup context

---

## Agents API

### Q: What are all the endpoints available in the Agents API and their use cases?

The Agents API provides these endpoints:
- `/agents`: Create, retrieve, update, delete agent definitions
- `/tasks`: Define and execute tasks, retrieve workflow definitions
- `/sessions`: Manage conversational sessions and conversation history
- `/executions`: Track task executions and monitor status
- `/docs`: Handle document storage, search, and retrieval with embeddings
- `/tools`: Define and manage agent tools
- `/users`: Manage user accounts and authentication
- `/responses`: OpenAI-compatible interface for LLM responses

### Q: How does session management work and what data is maintained per session?

Session management maintains conversation state:
- **Session Data**: `id`, `agent_id`, `user_id`, `created_at`, situation context
- **Entries**: Individual conversation turns with role, content, and timestamps
- Sessions created with `julep.sessions.create` linking agent and user
- Messages added via `julep.sessions.chat` with role and content
- Pagination support for retrieving conversation history

### Q: What are the different types of tools an agent can use and how are they configured?

Tool types available:
- **Web Search Tool**: Performs web searches with domain filtering
- **Function Tools**: OpenAI-compatible function calling format
- **System Tools**: Internal Julep resources (e.g., `create_julep_session`, `session_chat`)
- **Integration Tools**: External services (e.g., BrowserBase, email providers)

Configuration includes name, type, description, and type-specific parameters.

### Q: How does document storage and retrieval work for agent knowledge bases?

Documents (`Doc` entities) provide agent knowledge:
- Stored in PostgreSQL with embeddings in `docs_embeddings_store`
- Owned by either Agent or User
- Three search methods: text-based, embedding-based, hybrid
- Document operations: create, retrieve, list, search
- Supports metadata filtering and pagination

### Q: What are the authentication and authorization mechanisms for the API?

Two authentication modes:

**Single-Tenant Mode:**
- Uses `AGENTS_API_KEY` for authentication
- Default developer ID assumed
- `X-Auth-Key` header required

**Multi-Tenant Mode:**
- JWT-based authentication via Gateway
- `X-Developer-Id` header for resource isolation
- Developer-specific data access control
- JWT must contain sub, email, exp, iat claims

### Q: How are agent instructions processed and validated?

- Instructions stored as string or array of strings
- Validated by Pydantic models from OpenAPI schemas
- Included in agent's `default_system_template`
- Dynamic rendering supports both single and array formats
- TypeSpec definitions ensure consistent structure

### Q: What are the rate limiting and quota management strategies?

Rate limiting and quota management are planned features:
- `max_free_sessions` and `max_free_executions` environment variables defined
- Implementation details not yet available
- Listed as future enhancement in roadmap

### Q: How does the API handle streaming responses for real-time interactions?

Streaming support is currently planned but not implemented:
- Open Responses API designed for OpenAI compatibility
- `stream` configuration option available
- Full streaming implementation pending

---

## Worker System & Integration

### Q: How does the worker system integrate with different LLM providers?

The Worker integrates with LLMs through LiteLLM Proxy:
- LiteLLM acts as unified interface to various providers
- Supports OpenAI, Anthropic, Gemini, Groq, OpenRouter
- Worker makes LLM calls via LiteLLM Proxy
- Configuration in `litellm-config.yaml`
- Handles authentication, routing, and caching

### Q: What are the system activities available and how do they work?

System activities include:
- **LLM Calls**: Through LiteLLM Proxy
- **Tool Operations**: Via Integration Service
- **Data Operations**: Reading/writing to Memory Store
- **PG Query Step**: Direct PostgreSQL queries
- Activities invoked with `StepContext` and appropriate definitions

### Q: How does Julep handle tool execution and external API calls?

Tool execution handled by Integration Service:
- **Integration Tools**: Connect to external services with provider/method specs
- **System Tools**: Operate on internal Julep resources
- `ToolCallStep` defines tool and arguments
- Worker invokes Integration Service for execution
- Examples: email sending, browser automation, document search

### Q: What is the sandboxing mechanism for Python expression evaluation?

Python expression sandboxing:
- `validate_py_expression` function validates expressions
- Identifies expressions starting with `$`, `_`, or containing `{{`
- Checks for syntax errors, undefined names, unsafe operations
- Limited scope with allowed names: `_`, `inputs`, `outputs`, `state`, `steps`
- Prevents dunder attribute access and unapproved function calls

### Q: How are integration credentials managed and secured?

Integration credentials managed through:
- Credentials stored in `setup` parameters of tool definitions
- API keys provided in task definition YAML
- Environment variables for service-level credentials
- No explicit encryption details documented

### Q: What are the patterns for building custom integrations?

Custom integrations defined as Tool entities:
- Type set to `integration`
- Specify `provider`, `method`, and `setup` parameters
- Include provider-specific configuration (API keys, endpoints)
- Used within Task workflows as ToolCallStep
- Examples: Browserbase, email providers, Cloudinary

### Q: How does the browser automation integration work?

Browser automation workflow:
1. Create Julep session for AI agent
2. Create browser session using Browserbase
3. Store session info (browser_session_id, connect_url)
4. Perform actions via `perform_browser_action` tool
5. Interactive loop with agent planning and execution
6. Screenshot capture for visual feedback

### Q: What are the performance optimizations for worker pools?

Worker performance optimizations:
- `TEMPORAL_MAX_CONCURRENT_ACTIVITIES` controls concurrency
- `TEMPORAL_MAX_ACTIVITIES_PER_SECOND` limits activity rate
- `GUNICORN_WORKERS` for integration service scaling
- Connection pooling and timeout configurations
- LiteLLM caching and parallel forwarding

---

## Development & Deployment

### Q: What is the recommended development workflow for building with Julep?

Development workflow uses Docker Compose with watch mode:
- Changes in source directories trigger automatic sync/restart
- `agents-api`: Watches `./agents_api` and `gunicorn_conf.py`
- `worker`: Watches `./agents_api` and `Dockerfile.worker`
- `integrations`: Watches its directory for changes
- Lock file or Dockerfile changes trigger rebuilds

### Q: How should developers set up their local environment for testing?

Local setup primarily uses Docker:
1. Create project directory: `mkdir julep-responses-api`
2. Download and edit `.env` file
3. Download Docker Compose file
4. Run containers: `docker compose up --watch`
5. Verify with `docker ps`

Alternative CLI installation available via `npx` or `uvx`.

### Q: What are the deployment options and best practices?

Deployment options:

**Single-Tenant Mode:**
- All users share context
- `SKIP_CHECK_DEVELOPER_HEADERS=True`
- Requires `AGENTS_API_KEY`

**Multi-Tenant Mode:**
- Isolated resources per developer
- `AGENTS_API_MULTI_TENANT_MODE: true`
- JWT validation via Gateway

**Best Practices:**
- Use environment variables for configuration
- Implement layered security (API keys, JWT tokens)
- Enable independent component scaling
- Configure appropriate connection pools

### Q: How does the TypeSpec code generation work and when to use it?

TypeSpec code generation:
- TypeSpec files define data models (e.g., `models.tsp`)
- `scripts/generate_openapi_code.sh` generates code
- Creates Pydantic models and OpenAPI schemas
- Edit TypeSpec files, not generated code
- Regenerate after model changes

### Q: What are the testing strategies for agents and workflows?

Testing strategies include:
- Unit tests for entities (agents, docs, sessions, etc.)
- Integration tests simulating scenarios
- Workflow tests using `unittest.mock.patch`
- Test fixtures for consistent data
- Ward framework for test organization

### Q: How to debug failed task executions and trace through workflows?

Debugging approach:
- Check Execution status and error field
- List transitions to trace execution flow
- Examine transition outputs and types
- Use LogStep for workflow logging
- Error transitions indicate failure points

### Q: What are the monitoring and observability features?

Limited monitoring information available:
- Execution state and transition logging
- No explicit monitoring features documented
- Prometheus and Grafana mentioned in architecture
- Detailed observability features not specified

### Q: How to handle database migrations in production?

Database migration information not explicitly documented:
- PostgreSQL used as primary database
- Migration files exist in memory-store
- Production migration process not detailed

---

## Performance & Optimization

### Q: What are the performance characteristics of different operations?

Performance characteristics:
- MapReduceStep supports sequential or parallel execution
- API response times reduced by 15% (per changelog)
- Parallel processing improves collection operations
- Connection pooling optimizes database access
- Caching planned for future optimization

### Q: How does Julep handle concurrent agent executions?

Concurrent execution handled through:
- TaskExecutionWorkflow with Temporal orchestration
- Worker pools for distributed execution
- State isolation per execution
- Temporal manages workflow concurrency
- StepContext provides execution isolation

### Q: What are the caching strategies employed across the system?

Current caching:
- LiteLLM Proxy implements request caching
- Redis used for LiteLLM cache storage
- Web Search Tool has result caching
- Advanced caching mechanisms planned

### Q: How to optimize memory usage for large conversation histories?

Memory optimization strategies:
- Pagination with `limit` and `offset` parameters
- Maximum limit of 1000 entries per request
- `search_window` for time-based filtering (default 4 weeks)
- Token counting per entry
- RemoteObject pattern for large data

### Q: What are the bottlenecks in the current architecture?

Potential bottlenecks:
- Large data retrieval without proper pagination
- Complex database queries on large tables
- Multi-tenancy query filtering overhead
- Temporal workflow state management at scale
- JSON aggregation in history queries

### Q: How does connection pooling work for database access?

Connection pooling configuration:
- `connection_lifetime`: 600 seconds
- `idle_timeout`: 180 seconds
- `max_connections`: 50
- `retries`: 1
- `use_prepared_statements`: true
- `POOL_MAX_SIZE` configurable (default: CPU count, max 10)

### Q: What are the best practices for writing efficient task definitions?

Best practices:
- Define clear input schemas
- Use modular workflow steps
- Implement proper error handling
- Avoid infinite loops in recursive patterns
- Use appropriate tool types
- Monitor execution status and transitions
- Leverage parallel processing where applicable

---

## Security & Compliance

### Q: How does Julep handle sensitive data and ensure data privacy?

Data privacy ensured through:
- Multi-tenant architecture with resource isolation
- Developer-specific data access via `developer_id`
- `X-Developer-Id` header for request routing
- Separate data storage per developer

### Q: What are the security measures for multi-tenant deployments?

Multi-tenant security:
- JWT-based authentication at Gateway
- JWT validation with required claims (sub, email, exp, iat)
- `X-Developer-Id` header enforcement
- Developer ID verification against database
- Resource isolation by developer

### Q: How are API keys and secrets managed throughout the system?

Secret management:
- Environment variables for service credentials
- API keys in tool setup parameters
- `AGENTS_API_KEY` and `JWT_SHARED_KEY` for auth
- LLM provider keys as environment variables
- No explicit encryption details provided

### Q: What audit logging capabilities are available?

Audit logging:
- Currently limited implementation
- Listed as planned feature in roadmap
- Usage tracking for LLM calls (tokens and costs)
- Comprehensive audit logging pending

### Q: How does Julep ensure secure execution of user-provided code?

Secure code execution through:
- Task-based workflow system with YAML definitions
- Controlled tool invocation with explicit permissions
- Python expression validation
- Structured workflow steps
- No arbitrary code execution

### Q: What are the network security considerations for deployment?

Network security:
- API key authentication for single-tenant
- JWT tokens for multi-tenant
- Gateway-level authentication
- HTTPS/TLS support implied
- Service-to-service communication within network

---

## Advanced Use Cases & Patterns

### Q: What are examples of complex multi-agent workflows?

**Browser Use Assistant:**
- Session initialization
- Browser session creation
- Interactive agent-browser loop
- Screenshot feedback
- Goal-oriented task completion

**Email Assistant:**
- Email input processing
- Query generation
- Documentation search
- Response generation
- Automated email sending

**Video Processing:**
- Natural language instructions
- Cloudinary integration
- Transformation generation
- Video processing execution

### Q: How to implement human-in-the-loop patterns?

Human-in-the-loop not explicitly documented:
- `WaitForInputStep` provides pause mechanism
- Session-based interactions allow user input
- No dedicated approval workflow patterns
- Can be built using existing primitives

### Q: What are the patterns for building conversational agents with memory?

Conversational memory patterns:
- Session and Entry entities maintain history
- `previous_response_id` links responses
- Session metadata and custom templates
- Persistent conversation state
- Context maintained across interactions

### Q: How to implement custom tool integrations?

Custom tool implementation:
1. Define Tool entity with type `integration`
2. Specify provider, method, setup parameters
3. Use `@function_tool` decorator for functions
4. Add to agent's tool list
5. Invoke via ToolCallStep in workflows

### Q: What are the best practices for handling structured data extraction?

Structured data handling:
- Tools accept and return structured JSON
- Evaluate steps process tool outputs
- Response objects contain structured data
- Pydantic models ensure data validation
- TypeSpec defines consistent schemas

### Q: How to build agents that can learn and adapt over time?

Learning/adaptation features limited:
- Agent instructions can be updated
- Metadata field allows dynamic information
- No explicit learning mechanisms
- Adaptation through instruction updates
- Memory through conversation history

### Q: What are the patterns for building agents that can collaborate?

Agent collaboration not documented:
- Current model focuses on single agents
- No inter-agent communication patterns
- Sessions link one agent to users
- Collaboration would require custom implementation

---

## Troubleshooting & Common Issues

### Q: What are the most common errors and how to resolve them?

**Python Expression Errors:**
- Syntax errors: Fix malformed expressions
- Undefined names: Use allowed names only
- Unsafe operations: Avoid dunder attributes
- Runtime errors: Check for division by zero
- Unsupported features: Avoid lambdas, walrus operator

**Schema Validation Errors:**
- Pydantic validation failures
- Adjust JSON to match expected schema

**Integration Errors:**
- ApplicationError for missing tools
- Verify tool definitions and availability

### Q: How to debug issues with task execution?

Debugging steps:
1. Check Execution status field
2. Review error messages in Execution object
3. List and examine transitions
4. Check transition outputs and types
5. Use LogStep for additional logging
6. Trace workflow step progression

### Q: What are the common performance problems and solutions?

Performance issues and solutions:
- **Large collections**: Use MapReduceStep parallelism
- **Rate limits**: Implement SleepStep delays
- **Memory usage**: Paginate large result sets
- **Database queries**: Ensure proper indexing
- **Concurrent execution**: Configure worker pools

### Q: How to handle edge cases in agent conversations?

Edge case handling:
- `IfElseWorkflowStep` for conditional logic
- `SwitchStep` for complex branching
- `WaitForInputStep` for user input
- `ErrorWorkflowStep` for invalid states
- Proper error handling in workflows

### Q: What are the known limitations and workarounds?

**Expression Limitations:**
- No set comprehensions, lambdas, walrus operator
- Use alternative Python constructs

**Backwards Compatibility:**
- Old expression formats supported
- Use `$` prefix for consistency

**ParallelStep Not Implemented:**
- Use MapReduceStep with parallelism instead

**Streaming Not Available:**
- Planned feature, not yet implemented

**Rate Limiting:**
- Basic environment variables defined
- Full implementation pending

---

## Additional Resources

- [System Architecture Wiki](https://deepwiki.com/wiki/julep-ai/julep#2)
- [Data Model Wiki](https://deepwiki.com/wiki/julep-ai/julep#2.2)
- [TaskExecutionWorkflow Wiki](https://deepwiki.com/wiki/julep-ai/julep#3)
- [Workflow Steps Wiki](https://deepwiki.com/wiki/julep-ai/julep#3.1)

This FAQ is generated from the Julep platform documentation and codebase analysis. For the most up-to-date information, please refer to the official Julep documentation and repository.