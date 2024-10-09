## agents-api Overview

The `agents-api` project forms the foundation of an agent management system, defining the structure and API capabilities for managing agents. It supports essential operations such as creating, updating, listing, and deleting agents, as well as managing associated documents, tools, and tasks. 

The system is modular, containing several key components that interact with a CozoDB database, perform CRUD operations, and handle tasks like memory management and external service integration.

## Modules

### 1. **Models**
   - **Purpose**: Encapsulates all database interactions with CozoDB, providing structured CRUD operations for various entities.
   - **Entities**: Agents, developers, documents, entries, memories, sessions, etc.

### 2. **Routers**
   - **Purpose**: Handles HTTP requests and directs them to the appropriate handler functions for operations related to agents, documents, etc.

### 3. **Dependencies**
   - **Purpose**: Houses essential components such as authentication, developer identification, and custom exception handling required for the API to function.

### 4. **Common Utilities**
   - **Purpose**: Provides utility functions for interacting with the Cozo API client, handling dates, time, and custom JSON operations.

### 5. **Activities**
   - **Purpose**: Facilitates memory management, relationship summarization, and generating insights from dialogues with agents.

### 6. **Clients**
   - **Purpose**: Contains classes and functions to interface with external services and APIs, abstracting external service details from the core application logic.

### 7. **Workers**
   - **Purpose**: Manages background tasks and enhances performance by offloading heavy tasks such as agent task executions.


## Getting Started with Development

1. **Clone the Repository**:
   - Retrieve the source code to your local environment.
3. **Install Dependencies**:
   - Run `npm install` or the relevant package manager to install the necessary modules.
5. **Run the Application**:
   - Use your development server (e.g., FastAPI or Node) to run the API for testing and development.

This serves as a concise overview for developers to understand the structure and operations of the `agents-api`.

## Schema

### Relation `agent_default_settings`
```
┌───┬────────────────────┬────────┬─────────┬─────────────┐
│   │ column             │ is_key │ type    │ has_default │
├───┼────────────────────┼────────┼─────────┼─────────────┤
│ 0 │ agent_id           │ True   │ Uuid    │ False       │
│ 1 │ frequency_penalty  │ False  │ Float   │ True        │
│ 2 │ presence_penalty   │ False  │ Float   │ True        │
│ 3 │ length_penalty     │ False  │ Float   │ True        │
│ 4 │ repetition_penalty │ False  │ Float   │ True        │
│ 5 │ top_p              │ False  │ Float   │ True        │
│ 6 │ temperature        │ False  │ Float   │ True        │
│ 7 │ min_p              │ False  │ Float   │ True        │
│ 8 │ preset             │ False  │ String? │ True        │
└───┴────────────────────┴────────┴─────────┴─────────────┘
```

### Relation `agents`
```
┌───┬──────────────┬────────┬──────────┬─────────────┐
│   │ column       │ is_key │ type     │ has_default │
├───┼──────────────┼────────┼──────────┼─────────────┤
│ 0 │ developer_id │ True   │ Uuid     │ False       │
│ 1 │ agent_id     │ True   │ Uuid     │ False       │
│ 2 │ name         │ False  │ String   │ False       │
│ 3 │ about        │ False  │ String   │ False       │
│ 4 │ instructions │ False  │ [String] │ True        │
│ 5 │ model        │ False  │ String   │ True        │
│ 6 │ created_at   │ False  │ Float    │ True        │
│ 7 │ updated_at   │ False  │ Float    │ True        │
│ 8 │ metadata     │ False  │ Json     │ True        │
└───┴──────────────┴────────┴──────────┴─────────────┘
```

### Relation `developers`
```
┌───┬──────────────┬────────┬──────────┬─────────────┐
│   │ column       │ is_key │ type     │ has_default │
├───┼──────────────┼────────┼──────────┼─────────────┤
│ 0 │ developer_id │ True   │ Uuid     │ False       │
│ 1 │ email        │ False  │ String   │ False       │
│ 2 │ active       │ False  │ Bool     │ True        │
│ 3 │ tags         │ False  │ [String] │ True        │
│ 4 │ settings     │ False  │ Json     │ False       │
│ 5 │ created_at   │ False  │ Float    │ True        │
│ 6 │ updated_at   │ False  │ Float    │ True        │
└───┴──────────────┴────────┴──────────┴─────────────┘
```

### Relation `docs`
```
┌───┬────────────┬────────┬────────┬─────────────┐
│   │ column     │ is_key │ type   │ has_default │
├───┼────────────┼────────┼────────┼─────────────┤
│ 0 │ owner_type │ True   │ String │ False       │
│ 1 │ owner_id   │ True   │ Uuid   │ False       │
│ 2 │ doc_id     │ True   │ Uuid   │ False       │
│ 3 │ title      │ False  │ String │ False       │
│ 4 │ created_at │ False  │ Float  │ True        │
│ 5 │ metadata   │ False  │ Json   │ True        │
└───┴────────────┴────────┴────────┴─────────────┘
```

### Relation `entries`
```
┌───┬─────────────┬────────┬─────────┬─────────────┐
│   │ column      │ is_key │ type    │ has_default │
├───┼─────────────┼────────┼─────────┼─────────────┤
│ 0 │ session_id  │ True   │ Uuid    │ False       │
│ 1 │ entry_id    │ True   │ Uuid    │ True        │
│ 2 │ source      │ True   │ String  │ False       │
│ 3 │ role        │ True   │ String  │ False       │
│ 4 │ name        │ True   │ String? │ True        │
│ 5 │ content     │ False  │ [Json]  │ False       │
│ 6 │ token_count │ False  │ Int     │ False       │
│ 7 │ tokenizer   │ False  │ String  │ False       │
│ 8 │ created_at  │ False  │ Float   │ True        │
│ 9 │ timestamp   │ False  │ Float   │ True        │
└───┴─────────────┴────────┴─────────┴─────────────┘
```

### Relation `executions`
```
┌───┬──────────────┬────────┬─────────┬─────────────┐
│   │ column       │ is_key │ type    │ has_default │
├───┼──────────────┼────────┼─────────┼─────────────┤
│ 0 │ task_id      │ True   │ Uuid    │ False       │
│ 1 │ execution_id │ True   │ Uuid    │ False       │
│ 2 │ status       │ False  │ String  │ True        │
│ 3 │ input        │ False  │ Json    │ False       │
│ 4 │ output       │ False  │ Json?   │ True        │
│ 5 │ error        │ False  │ String? │ True        │
│ 6 │ session_id   │ False  │ Uuid?   │ True        │
│ 7 │ metadata     │ False  │ Json    │ True        │
│ 8 │ created_at   │ False  │ Float   │ True        │
│ 9 │ updated_at   │ False  │ Float   │ True        │
└───┴──────────────┴────────┴─────────┴─────────────┘
```

### Relation `memories`
```
┌───┬──────────────────┬────────┬────────────┬─────────────┐
│   │ column           │ is_key │ type       │ has_default │
├───┼──────────────────┼────────┼────────────┼─────────────┤
│ 0 │ memory_id        │ True   │ Uuid       │ False       │
│ 1 │ content          │ False  │ String     │ False       │
│ 2 │ last_accessed_at │ False  │ Float?     │ True        │
│ 3 │ timestamp        │ False  │ Float      │ True        │
│ 4 │ sentiment        │ False  │ Int        │ True        │
│ 5 │ entities         │ False  │ [Json]     │ True        │
│ 6 │ created_at       │ False  │ Float      │ True        │
│ 7 │ embedding        │ False  │ <F32;768>? │ True        │
└───┴──────────────────┴────────┴────────────┴─────────────┘
```

### Relation `memory_lookup`
```
┌───┬───────────┬────────┬───────┬─────────────┐
│   │ column    │ is_key │ type  │ has_default │
├───┼───────────┼────────┼───────┼─────────────┤
│ 0 │ agent_id  │ True   │ Uuid  │ False       │
│ 1 │ user_id   │ True   │ Uuid? │ True        │
│ 2 │ memory_id │ True   │ Uuid  │ False       │
└───┴───────────┴────────┴───────┴─────────────┘
```

### Relation `relations`
```
┌───┬──────────┬────────┬────────┬─────────────┐
│   │ column   │ is_key │ type   │ has_default │
├───┼──────────┼────────┼────────┼─────────────┤
│ 0 │ head     │ True   │ Uuid   │ False       │
│ 1 │ relation │ True   │ String │ False       │
│ 2 │ tail     │ True   │ Uuid   │ False       │
└───┴──────────┴────────┴────────┴─────────────┘
```

### Relation `session_cache`
```
┌───┬────────┬────────┬────────┬─────────────┐
│   │ column │ is_key │ type   │ has_default │
├───┼────────┼────────┼────────┼─────────────┤
│ 0 │ key    │ True   │ String │ False       │
│ 1 │ value  │ False  │ Json   │ False       │
└───┴────────┴────────┴────────┴─────────────┘
```

### Relation `session_lookup`
```
┌───┬──────────────────┬────────┬────────┬─────────────┐
│   │ column           │ is_key │ type   │ has_default │
├───┼──────────────────┼────────┼────────┼─────────────┤
│ 0 │ session_id       │ True   │ Uuid   │ False       │
│ 1 │ participant_type │ True   │ String │ False       │
│ 2 │ participant_id   │ True   │ Uuid   │ False       │
└───┴──────────────────┴────────┴────────┴─────────────┘
```

### Relation `sessions`
```
┌───┬──────────────────┬────────┬──────────┬─────────────┐
│   │ column           │ is_key │ type     │ has_default │
├───┼──────────────────┼────────┼──────────┼─────────────┤
│ 0 │ developer_id     │ True   │ Uuid     │ False       │
│ 1 │ session_id       │ True   │ Uuid     │ False       │
│ 2 │ updated_at       │ True   │ Validity │ True        │
│ 3 │ situation        │ False  │ String   │ False       │
│ 4 │ summary          │ False  │ String?  │ True        │
│ 5 │ created_at       │ False  │ Float    │ True        │
│ 6 │ metadata         │ False  │ Json     │ True        │
│ 7 │ render_templates │ False  │ Bool     │ True        │
│ 8 │ token_budget     │ False  │ Int?     │ True        │
│ 9 │ context_overflow │ False  │ String?  │ True        │
└───┴──────────────────┴────────┴──────────┴─────────────┘
```

### Relation `snippets`
```
┌───┬───────────┬────────┬─────────────┬─────────────┐
│   │ column    │ is_key │ type        │ has_default │
├───┼───────────┼────────┼─────────────┼─────────────┤
│ 0 │ doc_id    │ True   │ Uuid        │ False       │
│ 1 │ index     │ True   │ Int         │ False       │
│ 2 │ content   │ False  │ String      │ False       │
│ 3 │ embedding │ False  │ <F32;1024>? │ True        │
└───┴───────────┴────────┴─────────────┴─────────────┘
```

### Relation `tasks`
```
┌────┬───────────────┬────────┬──────────┬─────────────┐
│    │ column        │ is_key │ type     │ has_default │
├────┼───────────────┼────────┼──────────┼─────────────┤
│ 0  │ agent_id      │ True   │ Uuid     │ False       │
│ 1  │ task_id       │ True   │ Uuid     │ False       │
│ 2  │ updated_at_ms │ True   │ Validity │ True        │
│ 3  │ name          │ False  │ String   │ False       │
│ 4  │ description   │ False  │ String?  │ True        │
│ 5  │ input_schema  │ False  │ Json     │ False       │
│ 6  │ tools         │ False  │ [Json]   │ True        │
│ 7  │ inherit_tools │ False  │ Bool     │ True        │
│ 8  │ workflows     │ False  │ [Json]   │ False       │
│ 9  │ created_at    │ False  │ Float    │ True        │
│ 10 │ metadata      │ False  │ Json     │ True        │
└────┴───────────────┴────────┴──────────┴─────────────┘
```

### Relation `temporal_executions_lookup`
```
┌───┬────────────────────────┬────────┬─────────┬─────────────┐
│   │ column                 │ is_key │ type    │ has_default │
├───┼────────────────────────┼────────┼─────────┼─────────────┤
│ 0 │ execution_id           │ True   │ Uuid    │ False       │
│ 1 │ id                     │ True   │ String  │ False       │
│ 2 │ run_id                 │ False  │ String? │ False       │
│ 3 │ first_execution_run_id │ False  │ String? │ False       │
│ 4 │ result_run_id          │ False  │ String? │ False       │
│ 5 │ created_at             │ False  │ Float   │ True        │
└───┴────────────────────────┴────────┴─────────┴─────────────┘
```

### Relation `tools`
```
┌───┬────────────┬────────┬────────┬─────────────┐
│   │ column     │ is_key │ type   │ has_default │
├───┼────────────┼────────┼────────┼─────────────┤
│ 0 │ agent_id   │ True   │ Uuid   │ False       │
│ 1 │ tool_id    │ True   │ Uuid   │ False       │
│ 2 │ type       │ False  │ String │ False       │
│ 3 │ name       │ False  │ String │ False       │
│ 4 │ spec       │ False  │ Json   │ False       │
│ 5 │ updated_at │ False  │ Float  │ True        │
│ 6 │ created_at │ False  │ Float  │ True        │
└───┴────────────┴────────┴────────┴─────────────┘
```

### Relation `transitions`
```
┌───┬───────────────┬────────┬───────────────┬─────────────┐
│   │ column        │ is_key │ type          │ has_default │
├───┼───────────────┼────────┼───────────────┼─────────────┤
│ 0 │ execution_id  │ True   │ Uuid          │ False       │
│ 1 │ transition_id │ True   │ Uuid          │ False       │
│ 2 │ type          │ False  │ String        │ False       │
│ 3 │ current       │ False  │ (String,Int)  │ False       │
│ 4 │ next          │ False  │ (String,Int)? │ False       │
│ 5 │ output        │ False  │ Json?         │ False       │
│ 6 │ task_token    │ False  │ String?       │ True        │
│ 7 │ metadata      │ False  │ Json          │ True        │
│ 8 │ created_at    │ False  │ Float         │ True        │
│ 9 │ updated_at    │ False  │ Float         │ True        │
└───┴───────────────┴────────┴───────────────┴─────────────┘
```

### Relation `users`
```
┌───┬──────────────┬────────┬────────┬─────────────┐
│   │ column       │ is_key │ type   │ has_default │
├───┼──────────────┼────────┼────────┼─────────────┤
│ 0 │ developer_id │ True   │ Uuid   │ False       │
│ 1 │ user_id      │ True   │ Uuid   │ False       │
│ 2 │ name         │ False  │ String │ False       │
│ 3 │ about        │ False  │ String │ False       │
│ 4 │ created_at   │ False  │ Float  │ True        │
│ 5 │ updated_at   │ False  │ Float  │ True        │
│ 6 │ metadata     │ False  │ Json   │ True        │
└───┴──────────────┴────────┴────────┴─────────────┘
```


