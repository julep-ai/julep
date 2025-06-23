"""
SQL utilities for safe query construction and SQL injection prevention.

This module provides utilities to safely construct SQL queries, preventing SQL injection
attacks through proper validation and sanitization of identifiers and dynamic query parts.

AIDEV-NOTE: Critical security module - prevents SQL injection in dynamic queries.
Use SafeQueryBuilder for complex queries, safe_format_query for simple ORDER BY.
Never use f-strings or .format() with user input in SQL queries!
"""

import re
from typing import Any, Literal

from beartype import beartype
from fastapi import HTTPException

# AIDEV-NOTE: Whitelist of allowed column names for sorting across different tables
ALLOWED_SORT_COLUMNS = {
    "created_at",
    "updated_at",
    "timestamp",
    "name",
    "title",
}

# AIDEV-NOTE: Regex pattern for valid SQL identifiers (alphanumeric + underscore, not starting with digit)
SQL_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


@beartype
def sanitize_identifier(identifier: str, identifier_type: str = "column") -> str:
    """
    Validates and sanitizes SQL identifiers (table names, column names) to prevent SQL injection.

    Args:
        identifier: The identifier to validate
        identifier_type: Type of identifier for error messages (e.g., "column", "table")

    Returns:
        The validated identifier

    Raises:
        HTTPException: If the identifier is invalid
    """
    if not identifier:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {identifier_type} name: cannot be empty",
        )

    # Check against regex pattern
    if not SQL_IDENTIFIER_PATTERN.match(identifier):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {identifier_type} name: '{identifier}'. Must contain only letters, numbers, and underscores, and cannot start with a number.",
        )

    # Check length (PostgreSQL limit is 63 characters)
    if len(identifier) > 63:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {identifier_type} name: '{identifier}' is too long (max 63 characters)",
        )

    # Check for SQL keywords (basic list, can be extended)
    sql_keywords = {
        "select",
        "insert",
        "update",
        "delete",
        "drop",
        "create",
        "alter",
        "table",
        "from",
        "where",
        "join",
        "union",
        "grant",
        "revoke",
    }
    if identifier.lower() in sql_keywords:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {identifier_type} name: '{identifier}' is a reserved SQL keyword",
        )

    return identifier


@beartype
def validate_sort_field(
    field: str, allowed_fields: set[str] | None = None, table_prefix: str = ""
) -> str:
    """
    Validates sort field names against a whitelist to prevent SQL injection.

    Args:
        field: The field name to validate
        allowed_fields: Set of allowed field names (defaults to ALLOWED_SORT_COLUMNS)
        table_prefix: Optional table prefix to prepend (e.g., "e." for "e.created_at")

    Returns:
        The validated field name with optional table prefix

    Raises:
        HTTPException: If the field is not in the allowed list
    """
    allowed = allowed_fields or ALLOWED_SORT_COLUMNS

    if field not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field: '{field}'. Allowed fields: {', '.join(sorted(allowed))}",
        )

    # Additional validation using sanitize_identifier
    sanitize_identifier(field, "sort field")

    return f"{table_prefix}{field}" if table_prefix else field


@beartype
def validate_sort_direction(direction: str) -> Literal["ASC", "DESC"]:
    """
    Validates sort direction to prevent SQL injection.

    Args:
        direction: The sort direction to validate

    Returns:
        The validated direction in uppercase

    Raises:
        HTTPException: If the direction is invalid
    """
    direction_upper = direction.upper()
    if direction_upper not in ("ASC", "DESC"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort direction: '{direction}'. Must be 'asc' or 'desc'",
        )
    return direction_upper  # type: ignore


class SafeQueryBuilder:
    """
    A utility class for safely building dynamic SQL queries.

    This class helps construct SQL queries with proper parameterization,
    avoiding SQL injection vulnerabilities.
    """

    def __init__(self, base_query: str, initial_params: list[Any] | None = None):
        """
        Initialize the query builder.

        Args:
            base_query: The base SQL query string
            initial_params: Initial list of query parameters
        """
        self.query_parts: list[str] = [base_query]
        self.params: list[Any] = initial_params or []
        self._param_counter = len(self.params)

    def add_condition(self, condition: str, *params: Any) -> "SafeQueryBuilder":
        """
        Add a WHERE condition with parameterized values.

        Args:
            condition: The condition string with placeholders (e.g., "user_id = {}" or "date BETWEEN {} AND {}")
            *params: The parameter values

        Returns:
            Self for method chaining
        """
        # Count the number of {} placeholders in the condition
        placeholder_count = condition.count("{}")
        if placeholder_count != len(params):
            msg = f"Expected {placeholder_count} parameters, got {len(params)}"
            raise ValueError(msg)

        # Replace each {} with the appropriate parameter placeholder
        formatted_condition = condition
        for param in params:
            self._param_counter += 1
            formatted_condition = formatted_condition.replace(
                "{}", f"${self._param_counter}", 1
            )
            self.params.append(param)

        self.query_parts.append(formatted_condition)
        return self

    def add_raw_condition(self, condition: str) -> "SafeQueryBuilder":
        """
        Add a raw SQL condition (use with caution, ensure it's validated).

        Args:
            condition: The raw SQL condition

        Returns:
            Self for method chaining
        """
        self.query_parts.append(condition)
        return self

    def add_order_by(
        self,
        field: str,
        direction: str = "ASC",
        allowed_fields: set[str] | None = None,
        table_prefix: str = "",
    ) -> "SafeQueryBuilder":
        """
        Add ORDER BY clause with validation.

        Args:
            field: The field to sort by
            direction: Sort direction (ASC/DESC)
            allowed_fields: Allowed field names for sorting
            table_prefix: Optional table prefix

        Returns:
            Self for method chaining
        """
        safe_field = validate_sort_field(field, allowed_fields, table_prefix)
        safe_direction = validate_sort_direction(direction)
        self.query_parts.append(f" ORDER BY {safe_field} {safe_direction}")
        return self

    def add_limit_offset(self, limit: int, offset: int) -> "SafeQueryBuilder":
        """
        Add LIMIT and OFFSET clauses.

        Args:
            limit: Maximum number of rows
            offset: Number of rows to skip

        Returns:
            Self for method chaining
        """
        self._param_counter += 1
        limit_param = f"${self._param_counter}"
        self._param_counter += 1
        offset_param = f"${self._param_counter}"

        self.query_parts.append(f" LIMIT {limit_param} OFFSET {offset_param}")
        self.params.extend([limit, offset])
        return self

    def build(self) -> tuple[str, list[Any]]:
        """
        Build the final query and parameters.

        Returns:
            Tuple of (query_string, parameters)
        """
        return ("".join(self.query_parts), self.params)


# AIDEV-NOTE: Helper function to safely format queries with dynamic sort fields
@beartype
def safe_format_query(
    query_template: str,
    *,
    sort_by: str | None = None,
    direction: str | None = None,
    allowed_sort_fields: set[str] | None = None,
    table_prefix: str = "",
    **kwargs: Any,
) -> str:
    """
    Safely format a query template with validated sort fields and direction.

    Args:
        query_template: The query template with {sort_by} and {direction} placeholders
        sort_by: The field to sort by
        direction: Sort direction
        allowed_sort_fields: Allowed fields for sorting
        table_prefix: Optional table prefix for sort field
        **kwargs: Additional template parameters

    Returns:
        The formatted query string
    """
    format_params = kwargs.copy()

    if sort_by is not None:
        format_params["sort_by"] = validate_sort_field(
            sort_by, allowed_sort_fields, table_prefix
        )

    if direction is not None:
        format_params["direction"] = validate_sort_direction(direction)

    return query_template.format(**format_params)
