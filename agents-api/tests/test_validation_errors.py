"""Tests for validation error handlers and suggestion generation in web.py."""

from agents_api.web import _format_location, _get_error_suggestions
import pytest

from .fixtures import make_request


@pytest.mark.asyncio
async def test_format_location_formats_error_location_paths_correctly():
    """format_location: formats error location paths correctly"""
    """Test the _format_location function formats error locations correctly."""
    # Test empty location
    assert _format_location([]) == ""

    # Test with 'body' prefix that should be removed
    assert _format_location(["body", "name"]) == "name"

    # Test with nested properties
    assert _format_location(["body", "user", "name"]) == "user.name"

    # Test with array indices
    assert _format_location(["body", "items", 0, "name"]) == "items[0].name"

    # Test more complex nesting
    assert (
        _format_location(["body", "data", "users", 2, "addresses", 1, "street"])
        == "data.users[2].addresses[1].street"
    )


@pytest.mark.asyncio
async def test_get_error_suggestions_generates_helpful_suggestions_for_missing_fields():
    """get_error_suggestions: generates helpful suggestions for missing fields"""
    """Test the _get_error_suggestions function generates useful suggestions for missing fields."""
    error = {"type": "missing"}
    suggestions = _get_error_suggestions(error)

    assert "fix" in suggestions
    assert "example" in suggestions
    assert "Add this required field" in suggestions["fix"]


@pytest.mark.asyncio
async def test_get_error_suggestions_generates_helpful_suggestions_for_type_errors():
    """get_error_suggestions: generates helpful suggestions for type errors"""
    """Test the _get_error_suggestions function generates useful suggestions for type errors."""
    # String type error
    error = {"type": "type_error", "expected_type": "string"}
    suggestions = _get_error_suggestions(error)

    assert "fix" in suggestions
    assert "example" in suggestions
    assert "string" in suggestions["fix"]
    assert suggestions["example"] == '"text value"'

    # Integer type error
    error = {"type": "type_error", "expected_type": "integer"}
    suggestions = _get_error_suggestions(error)

    assert "fix" in suggestions
    assert "example" in suggestions
    assert "integer" in suggestions["fix"]
    assert suggestions["example"] == "42"


@pytest.mark.asyncio
async def test_get_error_suggestions_generates_helpful_suggestions_for_string_length_errors():
    """get_error_suggestions: generates helpful suggestions for string length errors"""
    """Test the _get_error_suggestions function generates useful suggestions for string length errors."""
    # Min length error
    error = {"type": "value_error.str.min_length", "limit_value": 5}
    suggestions = _get_error_suggestions(error)

    assert "fix" in suggestions
    assert "example" in suggestions
    assert "at least 5 characters" in suggestions["fix"]
    assert suggestions["example"] == "xxxxx"

    # Max length error
    error = {"type": "value_error.str.max_length", "limit_value": 10}
    suggestions = _get_error_suggestions(error)

    assert "fix" in suggestions
    assert "note" in suggestions
    assert "at most 10 characters" in suggestions["fix"]


@pytest.mark.asyncio
async def test_get_error_suggestions_generates_helpful_suggestions_for_number_range_errors():
    """get_error_suggestions: generates helpful suggestions for number range errors"""
    """Test the _get_error_suggestions function generates useful suggestions for number range errors."""
    # Min value error
    error = {"type": "value_error.number.not_ge", "limit_value": 5}
    suggestions = _get_error_suggestions(error)

    assert "fix" in suggestions
    assert "example" in suggestions
    assert "greater than or equal to 5" in suggestions["fix"]
    assert suggestions["example"] == "5"

    # Max value error
    error = {"type": "value_error.number.not_le", "limit_value": 100}
    suggestions = _get_error_suggestions(error)

    assert "fix" in suggestions
    assert "example" in suggestions
    assert "less than or equal to 100" in suggestions["fix"]
    assert suggestions["example"] == "100"


@pytest.mark.asyncio
async def test_validation_error_handler_returns_formatted_error_response_for_validation_errors(make_request=make_request):
    """validation_error_handler: returns formatted error response for validation errors"""
    """Test that validation errors return a well-formatted error response with helpful suggestions."""
    # Create an invalid request to trigger a validation error
    response = make_request(
        method="POST",
        url="/agents",
        json={
            # Missing required 'name' field
            # 'name': 'Test Agent',
            "about": "Test agent description",
            "model": "invalid-model-id",  # Invalid model ID
            "metadata": "not-an-object",  # Type error, should be an object
        },
    )

    # Verify response has expected status code
    assert response.status_code == 422

    # Verify response has the correct structure
    data = response.json()
    assert "error" in data
    assert "message" in data["error"]
    assert "details" in data["error"]
    assert "code" in data["error"]

    # Verify error details contain helpful suggestions
    details = data["error"]["details"]
    assert isinstance(details, list)
    assert len(details) > 0

    # Check for at least one error with a fix suggestion
    has_fix = False
    for error in details:
        if "fix" in error:
            has_fix = True
            break

    assert has_fix, "Expected at least one error with a 'fix' suggestion"


@test(
    "validation_error_suggestions: function generates helpful suggestions for all error types"
)
async def _():
    """Test that _get_error_suggestions handles all potential error types appropriately."""
    from agents_api.web import _get_error_suggestions

    # Test a variety of error types to ensure they all return helpful suggestions
    error_types = [
        "missing",
        "type_error",
        "value_error.missing",
        "value_error.extra",
        "value_error.const",
        "value_error.str.min_length",
        "value_error.str.max_length",
        "value_error.any_str.min_length",
        "value_error.any_str.max_length",
        "value_error.number.not_ge",
        "value_error.number.not_le",
        "value_error.number.not_gt",
        "value_error.number.not_lt",
        "enum",
        "json",
        "uuid",
        "datetime",
        "url",
        "email",
    ]

    # All these error types should generate non-empty suggestions
    for error_type in error_types:
        error = {"type": error_type}

        # Add additional info for specific error types
        if (
            "limit_value" in error_type
            or "min_length" in error_type
            or "max_length" in error_type
            or "not_ge" in error_type
            or "not_le" in error_type
            or "not_gt" in error_type
            or "not_lt" in error_type
        ):
            error["limit_value"] = 10
        elif "const" in error_type or "enum" in error_type:
            error["permitted"] = ["value1", "value2"]
        elif "expected_type" in error_type or error_type == "type_error":
            error["expected_type"] = "string"

        suggestions = _get_error_suggestions(error)

        # Each error type should generate at least some suggestions
        assert suggestions, f"No suggestions generated for error type: {error_type}"

        # At least the "fix" key should be present
        assert "fix" in suggestions, f"No 'fix' suggestion for error type: {error_type}"
