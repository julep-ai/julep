"""
Tests for SQL injection prevention mechanisms.

This module tests the SQL utilities and query builders to ensure they properly
prevent SQL injection attacks through various attack vectors.
"""

from agents_api.queries.sql_utils import (
    SafeQueryBuilder,
    safe_format_query,
    sanitize_identifier,
    validate_sort_direction,
    validate_sort_field,
)
from fastapi import HTTPException
from ward import raises, test


@test("sanitize_identifier: valid identifiers pass through unchanged")
def test_valid_identifiers():
    assert sanitize_identifier("column_name") == "column_name"
    assert sanitize_identifier("_private_column") == "_private_column"
    assert sanitize_identifier("column123") == "column123"
    assert sanitize_identifier("CamelCase") == "CamelCase"


@test("sanitize_identifier: empty string raises HTTPException")
def test_empty_identifier():
    with raises(HTTPException) as exc_info:
        sanitize_identifier("")
    assert exc_info.raised.status_code == 400
    assert "cannot be empty" in exc_info.raised.detail


@test("sanitize_identifier: identifiers starting with numbers are rejected")
def test_identifier_starting_with_number():
    with raises(HTTPException) as exc_info:
        sanitize_identifier("123column")
    assert exc_info.raised.status_code == 400


@test("sanitize_identifier: identifiers with spaces are rejected")
def test_identifier_with_spaces():
    with raises(HTTPException) as exc_info:
        sanitize_identifier("column name")
    assert exc_info.raised.status_code == 400


@test("sanitize_identifier: identifiers with special chars are rejected")
def test_identifier_with_special_chars():
    with raises(HTTPException) as exc_info:
        sanitize_identifier("column-name")
    assert exc_info.raised.status_code == 400


@test("sanitize_identifier: SQL injection attempts are blocked")
def test_sql_injection_attempts():
    with raises(HTTPException):
        sanitize_identifier("column; DROP TABLE users;--")

    with raises(HTTPException):
        sanitize_identifier("column' OR '1'='1")


@test("sanitize_identifier: SQL keywords are rejected")
def test_sql_keywords():
    keywords = ["select", "SELECT", "drop", "DROP", "table", "TABLE"]
    for keyword in keywords:
        with raises(HTTPException) as exc_info:
            sanitize_identifier(keyword)
        assert exc_info.raised.status_code == 400
        assert "reserved SQL keyword" in exc_info.raised.detail


@test("sanitize_identifier: identifiers exceeding 63 chars are rejected")
def test_length_limit():
    long_name = "a" * 64  # PostgreSQL limit is 63 characters
    with raises(HTTPException) as exc_info:
        sanitize_identifier(long_name)
    assert exc_info.raised.status_code == 400
    assert "too long" in exc_info.raised.detail


@test("validate_sort_field: allowed fields pass validation")
def test_allowed_sort_fields():
    assert validate_sort_field("created_at") == "created_at"
    assert validate_sort_field("updated_at") == "updated_at"
    assert validate_sort_field("timestamp") == "timestamp"


@test("validate_sort_field: custom allowed fields work correctly")
def test_custom_allowed_fields():
    custom_fields = {"custom_field", "another_field"}
    assert validate_sort_field("custom_field", custom_fields) == "custom_field"


@test("validate_sort_field: table prefixes are properly added")
def test_table_prefix():
    assert validate_sort_field("created_at", table_prefix="t.") == "t.created_at"
    assert validate_sort_field("updated_at", table_prefix="users.") == "users.updated_at"


@test("validate_sort_field: invalid fields raise HTTPException")
def test_invalid_sort_fields():
    with raises(HTTPException) as exc_info:
        validate_sort_field("invalid_field")
    assert exc_info.raised.status_code == 400
    assert "Invalid sort field" in exc_info.raised.detail


@test("validate_sort_field: SQL injection in field names is blocked")
def test_sort_field_sql_injection():
    with raises(HTTPException):
        validate_sort_field("created_at; DROP TABLE users;--")


@test("validate_sort_direction: valid directions are normalized")
def test_valid_sort_directions():
    assert validate_sort_direction("asc") == "ASC"
    assert validate_sort_direction("ASC") == "ASC"
    assert validate_sort_direction("desc") == "DESC"
    assert validate_sort_direction("DESC") == "DESC"


@test("validate_sort_direction: invalid directions raise HTTPException")
def test_invalid_sort_directions():
    invalid_directions = ["ascending", "descending", "up", "down", "", "'; DROP TABLE--"]
    for direction in invalid_directions:
        with raises(HTTPException) as exc_info:
            validate_sort_direction(direction)
        assert exc_info.raised.status_code == 400
        assert "Invalid sort direction" in exc_info.raised.detail


@test("SafeQueryBuilder: basic query construction works")
def test_basic_query_building():
    builder = SafeQueryBuilder("SELECT * FROM users WHERE 1=1")
    builder.add_condition(" AND name = {}", "John")
    builder.add_condition(" AND age > {}", 25)

    query, params = builder.build()
    assert query == "SELECT * FROM users WHERE 1=1 AND name = $1 AND age > $2"
    assert params == ["John", 25]


@test("SafeQueryBuilder: works with initial parameters")
def test_query_with_initial_params():
    builder = SafeQueryBuilder("SELECT * FROM users WHERE company_id = $1", [123])
    builder.add_condition(" AND active = {}", True)

    query, params = builder.build()
    assert query == "SELECT * FROM users WHERE company_id = $1 AND active = $2"
    assert params == [123, True]


@test("SafeQueryBuilder: ORDER BY clause with validation")
def test_order_by_clause():
    builder = SafeQueryBuilder("SELECT * FROM users")
    builder.add_order_by("created_at", "desc")

    query, _ = builder.build()
    assert "ORDER BY created_at DESC" in query


@test("SafeQueryBuilder: ORDER BY with custom fields and table prefix")
def test_order_by_custom_fields():
    builder = SafeQueryBuilder("SELECT * FROM posts")
    builder.add_order_by(
        "published_at", "asc", allowed_fields={"published_at", "title"}, table_prefix="p."
    )

    query, _ = builder.build()
    assert "ORDER BY p.published_at ASC" in query


@test("SafeQueryBuilder: LIMIT and OFFSET clauses")
def test_limit_offset():
    builder = SafeQueryBuilder("SELECT * FROM users")
    builder.add_limit_offset(10, 20)

    query, params = builder.build()
    assert "LIMIT $1 OFFSET $2" in query
    assert params == [10, 20]


@test("SafeQueryBuilder: complex query with multiple operations")
def test_complex_query():
    builder = SafeQueryBuilder("SELECT * FROM documents WHERE developer_id = $1", ["uuid-123"])
    builder.add_condition(" AND status = {}", "active")
    builder.add_condition(" AND created_at > {}", "2024-01-01")
    builder.add_order_by("created_at", "desc")
    builder.add_limit_offset(50, 0)

    query, params = builder.build()
    expected = (
        "SELECT * FROM documents WHERE developer_id = $1"
        " AND status = $2"
        " AND created_at > $3"
        " ORDER BY created_at DESC"
        " LIMIT $4 OFFSET $5"
    )
    assert query == expected
    assert params == ["uuid-123", "active", "2024-01-01", 50, 0]


@test("safe_format_query: basic query template formatting")
def test_basic_formatting():
    template = "SELECT * FROM users ORDER BY {sort_by} {direction}"
    result = safe_format_query(template, sort_by="created_at", direction="desc")
    assert result == "SELECT * FROM users ORDER BY created_at DESC"


@test("safe_format_query: formatting with table prefix")
def test_format_with_table_prefix():
    template = "SELECT * FROM users u ORDER BY {sort_by} {direction}"
    result = safe_format_query(
        template, sort_by="updated_at", direction="asc", table_prefix="u."
    )
    assert result == "SELECT * FROM users u ORDER BY u.updated_at ASC"


@test("safe_format_query: SQL injection via sort_by is prevented")
def test_format_sql_injection_sort_by():
    template = "SELECT * FROM users ORDER BY {sort_by} {direction}"

    with raises(HTTPException):
        safe_format_query(template, sort_by="created_at; DROP TABLE users;--", direction="asc")


@test("safe_format_query: SQL injection via direction is prevented")
def test_format_sql_injection_direction():
    template = "SELECT * FROM users ORDER BY {sort_by} {direction}"

    with raises(HTTPException):
        safe_format_query(template, sort_by="created_at", direction="asc; DROP TABLE users;--")


@test("safe_format_query: custom allowed fields work correctly")
def test_format_custom_allowed_fields():
    template = "SELECT * FROM posts ORDER BY {sort_by} {direction}"
    result = safe_format_query(
        template,
        sort_by="published_at",
        direction="desc",
        allowed_sort_fields={"published_at", "author_id", "title"},
    )
    assert result == "SELECT * FROM posts ORDER BY published_at DESC"


@test("safe_format_query: non-allowed fields are rejected")
def test_format_non_allowed_field():
    template = "SELECT * FROM posts ORDER BY {sort_by} {direction}"

    with raises(HTTPException):
        safe_format_query(
            template,
            sort_by="created_at",  # Not in allowed_sort_fields
            direction="desc",
            allowed_sort_fields={"published_at", "author_id", "title"},
        )
