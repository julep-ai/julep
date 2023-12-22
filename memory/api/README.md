# Memory API

*****

### Rough notes

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
