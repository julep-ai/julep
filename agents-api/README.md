# agents-api

## Overview

The `agents-api` project serves as the foundation of the agent management system, defining the structure and capabilities of the API that manages agents. It includes operations such as creating, updating, listing, and deleting agents, as well as managing documents and tools associated with these agents.

## Modules

### Models

The `models` module encapsulates all data interactions with the CozoDB database, providing a structured way to perform CRUD operations and other specific data manipulations across various entities.

### Routers

The `routers` module handles HTTP routing for different parts of the application, directing incoming HTTP requests to the appropriate handler functions.

### Dependencies

This module contains components crucial for the operation of the agents-api, including authentication, developer identification, and custom exception handling.

### Common Utilities

The `utils` module offers a collection of utility functions designed to support various aspects of the application, including interactions with the Cozo API client, date and time operations, and custom JSON utilities.

### Activities

The `activities` module facilitates various activities related to agent interactions, such as memory management, generating insights from dialogues, and summarizing relationships.

### Clients

The `clients` module contains client classes and functions for interacting with various external services and APIs, providing a simplified interface for the rest of the application.

### Workers

This module is responsible for handling background tasks and jobs for the Agents API application, enhancing the application's performance and scalability.

## Getting Started

To set up the project for development:

1. Clone the repository.
2. Install dependencies.
3. Run the application.

This guide provides a brief overview for new contributors to get started with the project development.

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


