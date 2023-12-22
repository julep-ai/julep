# Memory API

*****

## Rough notes

#### DIRECTORY CONVENTION

- `memory_api/models/{relation_prefix}/`
  + `__init__.py`
  + `schema.py`  # DDL
  + `{create|read|update|delete}_something.py`  # DML

- one query per file

- *relation_prefix* should be singular like `agent`, `user`, etc
- for example: `agent/` will include:
  - `agents`
  - `agent_jobs`
  - ...

## Phases

**CURRENT**: phase 1 (WIP)

### phase 1 (naive):
- all entries { source == "api_user" || source == "api_response" }
- use entries.tokenizer = "char_count"
- entries.token_count = len(json.dumps({name, role, content})) // 3.5
- entries.source can be one of "api_user" | "api_response"

> finalized relations
>   + agents
>   + users
>   + sessions
>   + session_lookup
>   + entries


### phase 1.5 (add instructions, tools etc NAIVELY)
- meaning no vector search, just dump em all
> finalized relations
>   + instructions
>   + tools

### phase 2 (procedural):
- all entries + vector_search(tools, instructions)
- need to embed and store

### phase 3 (remo):
- all entries that are root nodes in summarization chain

### phase 4 (additional_info):
- 

### phase 5 (add lm cache + models + tokenizer):
- 

### phase 6 (episodic mem):
- 

### phase 7 (implicit mem):
- 
