"""
Tests for metadata filter utility functions to prevent SQL injection
"""

from agents_api.queries.utils import build_metadata_filter_conditions
from ward import test


@test("utility: build_metadata_filter_conditions with empty filter")
async def _():
    """Test the build_metadata_filter_conditions utility with empty metadata filter."""
    base_params = ["param1", "param2"]
    metadata_filter = {}

    conditions, params = build_metadata_filter_conditions(base_params, metadata_filter)

    # Should return empty string and unchanged params
    assert conditions == ""
    assert params == base_params
    # Note: The implementation doesn't copy the params if there's no metadata filter
    # So we skip the identity check


@test("utility: build_metadata_filter_conditions with simple filter")
async def _():
    """Test the build_metadata_filter_conditions utility with simple metadata filter."""
    base_params = ["param1", "param2"]
    metadata_filter = {"key": "value"}

    conditions, params = build_metadata_filter_conditions(base_params, metadata_filter)

    # Should build a proper condition and append params
    assert conditions == " AND metadata->>$3 = $4"
    assert params == ["param1", "param2", "key", "value"]


@test("utility: build_metadata_filter_conditions with multiple filters")
async def _():
    """Test the build_metadata_filter_conditions utility with multiple metadata filters."""
    base_params = ["param1", "param2"]
    metadata_filter = {"key1": "value1", "key2": "value2"}

    conditions, params = build_metadata_filter_conditions(base_params, metadata_filter)

    # Should build compound condition and append all params
    assert conditions == " AND metadata->>$3 = $4 AND metadata->>$5 = $6"
    assert params == ["param1", "param2", "key1", "value1", "key2", "value2"]


@test("utility: build_metadata_filter_conditions with table alias")
async def _():
    """Test the build_metadata_filter_conditions with table alias."""
    base_params = ["param1", "param2"]
    metadata_filter = {"key": "value"}
    table_alias = "d."

    conditions, params = build_metadata_filter_conditions(
        base_params, metadata_filter, table_alias
    )

    # Should include table alias in condition
    assert conditions == " AND d.metadata->>$3 = $4"
    assert params == ["param1", "param2", "key", "value"]


@test("utility: build_metadata_filter_conditions with SQL injection attempts")
async def _():
    """Test that the build_metadata_filter_conditions prevents SQL injection."""
    base_params = ["param1", "param2"]

    # Test with SQL injection attempts in metadata keys and values
    metadata_filters = [
        {"key' OR 1=1--": "value"},
        {"key": "value' OR 1=1--"},
        {"key DROP TABLE users--": "value"},
        {"key": "value'; DROP TABLE users--"},
        {"key": "1' UNION SELECT * FROM users--"},
    ]

    for metadata_filter in metadata_filters:
        conditions, params = build_metadata_filter_conditions(base_params, metadata_filter)

        # Each key-value pair should be properly parameterized, not included in the SQL directly
        for key, value in metadata_filter.items():
            assert key in params  # Key should be in params, not in SQL string
            assert value in params  # Value should be in params, not in SQL string
            assert key not in conditions  # Key should not be in the SQL string
            assert value not in conditions  # Value should not be in the SQL string

        # The condition should only contain parameters, not the actual values
        for i in range(len(base_params) + 1, len(params) + 1):
            assert f"${i}" in conditions
