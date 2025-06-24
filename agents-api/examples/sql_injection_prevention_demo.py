#!/usr/bin/env python3
"""
SQL Injection Prevention Demo

This script demonstrates how the SQL injection prevention mechanisms work
in the agents-api queries module.
"""

import sys

sys.path.insert(0, ".")

from agents_api.queries.sql_utils import (
    SafeQueryBuilder,
    safe_format_query,
    validate_sort_field,
)


def demonstrate_safe_query_building():
    """Demonstrate safe query building with SafeQueryBuilder."""
    print("=== SafeQueryBuilder Demo ===\n")

    # Example 1: Basic safe query construction
    print("1. Basic safe query construction:")
    builder = SafeQueryBuilder("SELECT * FROM agents WHERE developer_id = $1", ["dev-123"])
    builder.add_condition(" AND name LIKE {}", "%test%")
    builder.add_condition(" AND created_at > {}", "2024-01-01")
    builder.add_order_by("created_at", "desc")
    builder.add_limit_offset(10, 0)

    query, params = builder.build()
    print(f"Query: {query}")
    print(f"Params: {params}")
    print()


def demonstrate_sql_injection_prevention():
    """Demonstrate how SQL injection attempts are prevented."""
    print("=== SQL Injection Prevention Demo ===\n")

    # Example 2: Preventing SQL injection in ORDER BY
    print("2. Attempting SQL injection in ORDER BY clause:")
    malicious_sort = "created_at; DROP TABLE agents;--"

    try:
        result = safe_format_query(
            "SELECT * FROM agents ORDER BY {sort_by} {direction}",
            sort_by=malicious_sort,
            direction="desc",
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"✓ Blocked: {type(e).__name__}: {e}")
    print()

    # Example 3: Preventing SQL injection in sort direction
    print("3. Attempting SQL injection in sort direction:")
    malicious_direction = "desc; DELETE FROM agents WHERE 1=1;--"

    try:
        result = safe_format_query(
            "SELECT * FROM agents ORDER BY {sort_by} {direction}",
            sort_by="created_at",
            direction=malicious_direction,
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"✓ Blocked: {type(e).__name__}: {e}")
    print()


def demonstrate_valid_usage():
    """Demonstrate valid usage of the SQL utilities."""
    print("=== Valid Usage Demo ===\n")

    # Example 4: Valid query formatting
    print("4. Valid query formatting with safe_format_query:")
    query = safe_format_query(
        "SELECT * FROM documents WHERE owner_id = $1 ORDER BY {sort_by} {direction}",
        sort_by="updated_at",
        direction="asc",
        allowed_sort_fields={"created_at", "updated_at", "title"},
    )
    print(f"Safe query: {query}")
    print()

    # Example 5: Complex query with metadata filters
    print("5. Complex query with SafeQueryBuilder:")
    builder = SafeQueryBuilder(
        """
        SELECT d.*, array_agg(t.tag) as tags
        FROM documents d
        LEFT JOIN document_tags dt ON d.id = dt.document_id
        LEFT JOIN tags t ON dt.tag_id = t.id
        WHERE d.developer_id = $1
    """,
        ["dev-456"],
    )

    builder.add_condition(" AND d.status = {}", "published")
    builder.add_condition(" AND d.created_at BETWEEN {} AND {}", "2024-01-01", "2024-12-31")
    builder.add_raw_condition(" GROUP BY d.id")
    builder.add_order_by(
        "created_at", "desc", allowed_fields={"created_at", "updated_at"}, table_prefix="d."
    )
    builder.add_limit_offset(20, 0)

    query, params = builder.build()
    print(f"Query: {query}")
    print(f"Params: {params}")
    print()


def demonstrate_whitelist_validation():
    """Demonstrate whitelist-based validation."""
    print("=== Whitelist Validation Demo ===\n")

    # Example 6: Field validation with custom whitelist
    print("6. Field validation with custom whitelist:")

    # Valid field
    try:
        field = validate_sort_field(
            "published_at", allowed_fields={"published_at", "author_name", "view_count"}
        )
        print(f"✓ Valid field accepted: {field}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Invalid field
    try:
        field = validate_sort_field(
            "secret_data", allowed_fields={"published_at", "author_name", "view_count"}
        )
        print(f"Field accepted: {field}")
    except Exception as e:
        print(f"✓ Invalid field blocked: {type(e).__name__}: {e}")
    print()


if __name__ == "__main__":
    print("SQL Injection Prevention Demonstration")
    print("=====================================\n")

    demonstrate_safe_query_building()
    demonstrate_sql_injection_prevention()
    demonstrate_valid_usage()
    demonstrate_whitelist_validation()

    print("\nConclusion:")
    print("-----------")
    print("The SQL injection prevention mechanisms ensure that:")
    print("1. All dynamic SQL parts are properly validated")
    print("2. User input is parameterized, not concatenated")
    print("3. Sort fields and directions are whitelisted")
    print("4. SQL keywords and special characters are blocked")
    print("5. Complex queries can be built safely without string concatenation")
