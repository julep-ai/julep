"""
SQL building utilities for safe dynamic query construction with asyncpg.

This module provides utilities to build SQL queries dynamically while preventing
SQL injection and handling type safety properly with asyncpg.
"""

from typing import Any, TypeVar

T = TypeVar("T")


class SQLBuilder:
    """
    A builder class for constructing SQL queries safely.

    This class helps build dynamic SQL queries by:
    - Properly parameterizing all values
    - Building UPDATE statements with only non-NULL fields
    - Handling SQL identifiers safely
    - Managing parameter placeholders correctly
    """

    def __init__(self):
        self.query_parts: list[str] = []
        self.params: list[Any] = []
        self._param_counter = 0

    def _next_param_placeholder(self) -> str:
        """Get the next parameter placeholder ($1, $2, etc.)"""
        self._param_counter += 1
        return f"${self._param_counter}"

    def add_param(self, value: Any) -> str:
        """Add a parameter and return its placeholder."""
        self.params.append(value)
        return self._next_param_placeholder()

    def safe_identifier(self, name: str) -> str:
        """
        Safely quote an SQL identifier (table/column name).

        Note: This is a simple implementation. In production, consider using
        a more robust identifier escaping mechanism.
        """
        # Special case for SELECT *
        if name == "*":
            return name

        # Basic validation - only allow alphanumeric, underscore, dot
        if not name.replace("_", "").replace(".", "").isalnum():
            msg = f"Invalid identifier: {name}"
            raise ValueError(msg)

        # Quote the identifier
        return f'"{name}"'

    def build_update_fields(
        self, fields: dict[str, Any], skip_none: bool = True
    ) -> tuple[str, list[Any]]:
        """
        Build UPDATE SET clause with dynamic fields.

        Args:
            fields: Dictionary of field_name -> value
            skip_none: If True, skip fields with None values

        Returns:
            Tuple of (SET clause, parameters list)
        """
        set_parts = []

        for field_name, value in fields.items():
            if skip_none and value is None:
                continue

            placeholder = self.add_param(value)
            set_parts.append(f"{self.safe_identifier(field_name)} = {placeholder}")

        if not set_parts:
            msg = "No fields to update"
            raise ValueError(msg)

        return " SET " + ", ".join(set_parts), self.params

    def build_where_clause(
        self, conditions: dict[str, Any], operator: str = "AND"
    ) -> tuple[str, list[Any]]:
        """
        Build WHERE clause from conditions.

        Args:
            conditions: Dictionary of field_name -> value
            operator: Logical operator (AND/OR)

        Returns:
            Tuple of (WHERE clause, parameters list)
        """
        where_parts = []

        for field_name, value in conditions.items():
            if value is None:
                where_parts.append(f"{self.safe_identifier(field_name)} IS NULL")
            else:
                placeholder = self.add_param(value)
                where_parts.append(
                    f"{self.safe_identifier(field_name)} = {placeholder}"
                )

        if not where_parts:
            return "", []

        return f" WHERE {f' {operator} '.join(where_parts)}", self.params

    def build_order_by(self, sort_field: str, direction: str = "ASC") -> str:
        """
        Build ORDER BY clause safely.

        Args:
            sort_field: Field to sort by
            direction: ASC or DESC

        Returns:
            ORDER BY clause
        """
        if direction.upper() not in ("ASC", "DESC"):
            msg = f"Invalid sort direction: {direction}"
            raise ValueError(msg)

        return f" ORDER BY {self.safe_identifier(sort_field)} {direction.upper()}"

    def build_limit_offset(
        self, limit: int | None = None, offset: int | None = None
    ) -> tuple[str, list[Any]]:
        """
        Build LIMIT/OFFSET clause.

        Args:
            limit: Maximum number of rows
            offset: Number of rows to skip

        Returns:
            Tuple of (LIMIT/OFFSET clause, parameters)
        """
        clause_parts = []
        params = []
        param_idx = len(self.params) + 1

        if limit is not None:
            clause_parts.append(f"LIMIT ${param_idx}")
            params.append(limit)
            param_idx += 1

        if offset is not None:
            clause_parts.append(f"OFFSET ${param_idx}")
            params.append(offset)

        return " " + " ".join(clause_parts) if clause_parts else "", params


def build_update_query(
    table_name: str,
    update_fields: dict[str, Any],
    where_conditions: dict[str, Any],
    returning: list[str] | None = None,
    param_offset: int = 0,
) -> tuple[str, list[Any]]:
    """
    Build a complete UPDATE query dynamically.

    Args:
        table_name: Name of the table to update
        update_fields: Fields to update (None values are skipped)
        where_conditions: WHERE clause conditions
        returning: List of fields to return
        param_offset: Starting parameter index (for queries with existing parameters)

    Returns:
        Tuple of (query string, parameters list)
    """
    builder = SQLBuilder()
    builder._param_counter = param_offset  # Start from offset

    # Build base UPDATE statement
    query = f"UPDATE {builder.safe_identifier(table_name)}"

    # Build SET clause
    set_clause, _ = builder.build_update_fields(update_fields)
    query += set_clause

    # Build WHERE clause
    where_clause, _ = builder.build_where_clause(where_conditions)
    if not where_clause:
        msg = "UPDATE without WHERE clause is not allowed"
        raise ValueError(msg)
    query += where_clause

    # Add RETURNING clause if needed
    if returning:
        query += " RETURNING " + ", ".join(
            builder.safe_identifier(field) for field in returning
        )

    # Return query and all collected parameters
    return query, builder.params


def build_select_with_optional_filters(
    base_query: str,
    optional_conditions: dict[str, tuple[str, Any]],
    base_params: list[Any],
) -> tuple[str, list[Any]]:
    """
    Build a SELECT query with optional filter conditions.

    Args:
        base_query: Base SELECT query with placeholders for optional conditions
        optional_conditions: Dict of placeholder -> (condition_sql, param_value)
        base_params: Base parameters for the query

    Returns:
        Tuple of (final query, all parameters)
    """
    query = base_query
    params = base_params.copy()

    for placeholder, (condition_sql, param_value) in optional_conditions.items():
        if param_value is not None:
            # Replace placeholder with actual condition
            param_idx = len(params) + 1
            actual_condition = condition_sql.replace("$PARAM", f"${param_idx}")
            query = query.replace(placeholder, actual_condition)
            params.append(param_value)
        else:
            # Remove placeholder
            query = query.replace(placeholder, "")

    return query, params


def build_jsonb_update_query(
    table_name: str,
    jsonb_column: str,
    updates: dict[str, Any],
    where_conditions: dict[str, Any],
    merge: bool = True,
) -> tuple[str, list[Any]]:
    """
    Build query to update JSONB fields.

    Args:
        table_name: Table name
        jsonb_column: Name of the JSONB column
        updates: Dictionary of updates to apply
        where_conditions: WHERE conditions
        merge: If True, merge with existing data; if False, replace

    Returns:
        Tuple of (query string, parameters)
    """
    builder = SQLBuilder()
    param_idx = 1

    # Build the UPDATE query
    query = f"UPDATE {builder.safe_identifier(table_name)} SET "

    if merge:
        # Merge with existing JSONB data
        query += f"{builder.safe_identifier(jsonb_column)} = {builder.safe_identifier(jsonb_column)} || ${param_idx}"
    else:
        # Replace JSONB data
        query += f"{builder.safe_identifier(jsonb_column)} = ${param_idx}"

    params = [updates]
    param_idx += 1

    # Add WHERE conditions
    where_parts = []
    for field, value in where_conditions.items():
        where_parts.append(f"{builder.safe_identifier(field)} = ${param_idx}")
        params.append(value)
        param_idx += 1

    query += " WHERE " + " AND ".join(where_parts)
    query += " RETURNING *"

    return query, params


# AIDEV-NOTE: Core utility for building type-safe dynamic SQL queries with asyncpg
def build_patch_query(
    table_name: str,
    patch_data: dict[str, Any],
    where_conditions: dict[str, Any],
    returning_fields: list[str] | None = None,
    special_handlers: dict[str, callable] | None = None,
    param_offset: int = 0,
) -> tuple[str, list[Any]]:
    """
    Build a PATCH-style update query that only updates non-None fields.

    This is a replacement for CASE/WHEN patterns that cause type issues.

    Args:
        table_name: Table to update
        patch_data: Fields to potentially update (None values are skipped)
        where_conditions: WHERE clause conditions
        returning_fields: Fields to return after update
        special_handlers: Dict of field_name -> handler function for special processing
        param_offset: Starting parameter index (for queries with existing parameters)

    Returns:
        Tuple of (query string, parameters list)
    """
    # Filter out None values
    update_fields = {}
    special_handlers = special_handlers or {}

    for field, value in patch_data.items():
        if value is not None:
            # Apply special handler if exists
            if field in special_handlers:
                value = special_handlers[field](value)
            update_fields[field] = value

    if not update_fields:
        # No fields to update - return a SELECT query instead
        builder = SQLBuilder()
        builder._param_counter = param_offset
        query = f"SELECT * FROM {builder.safe_identifier(table_name)}"
        where_clause, params = builder.build_where_clause(where_conditions)
        query += where_clause
        return query, params

    # Build the UPDATE query
    return build_update_query(
        table_name=table_name,
        update_fields=update_fields,
        where_conditions=where_conditions,
        returning=returning_fields or ["*"],
        param_offset=param_offset,
    )
