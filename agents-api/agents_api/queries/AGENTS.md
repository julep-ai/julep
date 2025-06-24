# AGENTS.md - queries

This folder contains database query builders and SQL files for `agents-api`.

Key Points
- Organize queries by domain under subfolders (agents, chat, tasks, etc.).
- Use asyncpg for execution and return typed Pydantic models.
- Validate SQL syntax with `poe check`.
- Add new queries in `queries/` and index them if needed.
- Tests reside under `agents-api/tests/`.
- Add `AIDEV-NOTE` anchors at the top of query modules to clarify module purpose.
- **ALWAYS use SQL safety utilities** from `sql_utils.py` to prevent SQL injection.

# Queries

## Purpose
- Database access layer for the application
- SQL query execution and result processing
- Organized by resource types matching API endpoints

## Key Query Modules

### projects/
- Create, list, and check for project existence
- Project association with resources

### agents/, tasks/, sessions/, users/
- CRUD operations for core resources
- Data validation and normalization
- Project association handling

### secrets/
- Secure storage and retrieval of sensitive data
- Key-value storage with encryption
- Access control and validation

### usage/
- Usage tracking and cost calculation
- User activity monitoring
- Billing and analytics data

### executions/
- Create and track task executions
- Handle execution transitions
- Map between Temporal workflows and API data

### docs/
- Document storage and retrieval
- Text search (search_docs_by_text)
- Embedding search (search_docs_by_embedding)
- Hybrid search combining both approaches

### entries/
- Record chat history and interactions
- Retrieve conversation history

## Common Patterns
- Async functions for database operations
- Connection pool management
- Data serialization/deserialization
- Pydantic model integration

## Usage Pattern
1. Query function receives parameters and optional connection_pool
2. SQL query construction (often with query parameters)
3. Execute query via asyncpg
4. Process results into Pydantic models
5. Return typed response

## Important Functions
- `prepare_execution_input`: Builds inputs for Temporal workflows
- `create_execution_transition`: Records state changes in executions
- `search_docs_hybrid`: Combined embedding and text search

## SQL Safety and Security

### SQL Injection Prevention
All queries MUST use the utilities from `sql_utils.py` to prevent SQL injection attacks:

1. **SafeQueryBuilder**: For complex queries with dynamic conditions
   ```python
   from ..sql_utils import SafeQueryBuilder
   
   builder = SafeQueryBuilder(base_query, initial_params)
   builder.add_condition(" AND status = {}", status_value)
   builder.add_order_by("created_at", "desc", allowed_fields={"created_at", "updated_at"})
   builder.add_limit_offset(limit, offset)
   query, params = builder.build()
   ```

2. **safe_format_query**: For simple queries with ORDER BY clauses
   ```python
   from ..sql_utils import safe_format_query
   
   query = safe_format_query(
       query_template,
       sort_by="created_at",
       direction="desc",
       allowed_sort_fields={"created_at", "updated_at", "name"},
       table_prefix="t."
   )
   ```

3. **validate_sort_field** and **validate_sort_direction**: For validating user inputs
   - Uses whitelisting approach
   - Validates against SQL identifier patterns
   - Prevents SQL keyword injection

### Never Do This
- ❌ NEVER use f-strings for SQL: `f"SELECT * FROM {table} WHERE {field} = '{value}'"`
- ❌ NEVER use .format() for SQL: `"SELECT * FROM {} WHERE {}".format(table, condition)`
- ❌ NEVER concatenate user input into SQL: `query + " ORDER BY " + user_input`

### Always Do This
- ✅ Use parameterized queries: `$1, $2, $3` placeholders
- ✅ Use SafeQueryBuilder for complex dynamic queries
- ✅ Validate all identifiers with sanitize_identifier()
- ✅ Whitelist allowed sort fields and directions

### Testing
- SQL injection prevention tests are in `tests/test_sql_injection_prevention.py`
- Run with: `poe test --search "sql_injection_prevention"`
- 27 comprehensive tests covering various attack vectors
