# SQL Injection Prevention in Agents API

## Overview

This document describes the SQL injection prevention mechanisms implemented in the agents-api to protect against malicious SQL injection attacks.

## Vulnerabilities Identified

During the security audit, the following SQL injection vulnerabilities were found:

1. **Direct String Interpolation**: Several query files used f-strings or `.format()` to directly interpolate user-controlled values into SQL queries, particularly in:
   - ORDER BY clauses (sort field and direction)
   - Dynamic query building with metadata filters
   - Table/column name references

2. **Affected Files**:
   - `queries/entries/list_entries.py`
   - `queries/docs/list_docs.py`
   - `queries/files/list_files.py`
   - `queries/docs/bulk_delete_docs.py`
   - `queries/agents/list_agents.py`

## Solution Implemented

### 1. SQL Utilities Module (`queries/sql_utils.py`)

Created a comprehensive SQL utilities module with the following components:

#### a. `sanitize_identifier()`
- Validates SQL identifiers (table/column names)
- Enforces alphanumeric + underscore pattern
- Blocks SQL keywords
- Enforces PostgreSQL 63-character limit

#### b. `validate_sort_field()` and `validate_sort_direction()`
- Whitelist-based validation for sort fields
- Ensures sort directions are only "ASC" or "DESC"
- Supports custom allowed field lists
- Adds table prefixes safely

#### c. `SafeQueryBuilder` Class
- Provides a safe way to build dynamic SQL queries
- All parameters are properly parameterized ($1, $2, etc.)
- Supports complex query construction without string concatenation
- Methods for adding conditions, ORDER BY, LIMIT/OFFSET safely

#### d. `safe_format_query()`
- Safe alternative to string formatting for query templates
- Validates all dynamic parts before formatting
- Primarily used for ORDER BY clauses

### 2. Updated Query Files

Modified vulnerable query files to use the new safety mechanisms:

- **list_entries.py**: Uses `safe_format_query()` for ORDER BY
- **list_docs.py**: Uses `SafeQueryBuilder` for entire query construction
- **list_files.py**: Uses `SafeQueryBuilder` for dynamic conditions
- **bulk_delete_docs.py**: Removed f-string usage, uses proper concatenation
- **list_agents.py**: Uses `.replace()` instead of `.format()` for metadata filter

### 3. Test Coverage

Added comprehensive test suite (`tests/test_sql_injection_prevention.py`) that verifies:
- Identifier sanitization
- SQL injection attempt blocking
- Whitelist validation
- Safe query building
- Complex query construction

## Usage Examples

### Basic Query Building
```python
from agents_api.queries.sql_utils import SafeQueryBuilder

builder = SafeQueryBuilder("SELECT * FROM users WHERE active = true")
builder.add_condition(" AND created_at > {}", "2024-01-01")
builder.add_order_by("created_at", "desc")
builder.add_limit_offset(10, 0)

query, params = builder.build()
# Result: SELECT * FROM users WHERE active = true AND created_at > $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3
# Params: ['2024-01-01', 10, 0]
```

### Safe ORDER BY Formatting
```python
from agents_api.queries.sql_utils import safe_format_query

query = safe_format_query(
    "SELECT * FROM entries ORDER BY {sort_by} {direction}",
    sort_by="timestamp",
    direction="desc",
    allowed_sort_fields={"created_at", "timestamp"}
)
# Result: SELECT * FROM entries ORDER BY timestamp DESC
```

### Preventing SQL Injection
```python
# This will raise HTTPException(400)
safe_format_query(
    "SELECT * FROM users ORDER BY {sort_by}",
    sort_by="created_at; DROP TABLE users;--"
)
```

## Best Practices

1. **Never use f-strings or .format() for SQL queries** with user input
2. **Always use parameterized queries** ($1, $2, etc.) for values
3. **Whitelist column/table names** that can be dynamically referenced
4. **Use SafeQueryBuilder** for complex dynamic query construction
5. **Validate all user input** before using in SQL queries

## Migration Guide

If you need to update other query files:

1. **For simple ORDER BY**:
   ```python
   # Before
   query = f"SELECT * FROM table ORDER BY {sort_by} {direction}"
   
   # After
   from ..sql_utils import safe_format_query
   query = safe_format_query(
       "SELECT * FROM table ORDER BY {sort_by} {direction}",
       sort_by=sort_by,
       direction=direction,
       allowed_sort_fields={"created_at", "updated_at"}
   )
   ```

2. **For complex dynamic queries**:
   ```python
   # Before
   query = base_query
   if condition:
       query += f" AND field = {value}"
   
   # After
   from ..sql_utils import SafeQueryBuilder
   builder = SafeQueryBuilder(base_query)
   if condition:
       builder.add_condition(" AND field = {}", value)
   query, params = builder.build()
   ```

## Security Considerations

- The whitelist approach ensures only pre-approved column names can be used
- All values are parameterized, preventing SQL injection via data
- SQL keywords and special characters in identifiers are blocked
- The 63-character limit prevents buffer overflow attacks
- HTTPException with 400 status provides clear error messages without exposing internals

## Future Improvements

1. Consider adding more SQL keywords to the blocklist
2. Add support for more complex query patterns if needed
3. Consider integrating with an SQL parser for even more robust validation
4. Add logging for blocked SQL injection attempts for security monitoring