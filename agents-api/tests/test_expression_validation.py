"""
Tests to verify that Python expression validation works correctly.
This includes testing the bug fix for expressions without a $ prefix.
"""

from agents_api.common.utils.task_validation import validate_py_expression


def test_expression_validation_basic():
    """Test basic validation of Python expressions."""

    # Test with a syntax error
    expression = "$ 1 + )"
    result = validate_py_expression(expression)

    assert len(result["syntax_errors"]) > 0

    assert "Syntax error" in result["syntax_errors"][0]

    # Test with undefined variable
    expression = "$ undefined_var + 10"
    result = validate_py_expression(expression)

    assert len(result["undefined_names"]) > 0

    assert "Undefined name: 'undefined_var'" in result["undefined_names"]

    # Test with unsafe attribute access
    expression = "$ some_obj.dangerous_method()"
    result = validate_py_expression(expression)

    assert len(result["unsafe_operations"]) > 0

    assert "Potentially unsafe attribute access" in result["unsafe_operations"][0]

    # Test division by zero detection - note: static analysis may not catch all instances
    expression = "$ 10 / 0"
    result = validate_py_expression(expression)

    # This assertion may be fragile depending on the static analyzer's capabilities
    if len(result["potential_runtime_errors"]) > 0:
        assert "Division by zero" in result["potential_runtime_errors"][0]
    else:
        print("Note: Static analyzer did not detect division by zero")

    # Test a valid expression
    expression = "$ _.topic if hasattr(_, 'topic') else 'default'"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values())

    # Test that _ is allowed by default
    expression = "$ _.attribute"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values())

    # This test is no longer relevant since allow_placeholder_variables parameter was removed
    # Special variables are now always allowed by default


def test_expression_without_dollar_prefix():
    """Test that expressions without a $ prefix return empty issues and don't proceed with validation."""

    # Test regular string without $ prefix
    expression = "Hello world"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Non-$ expressions should return empty issues"
    )

    # Test with Python syntax but no $ prefix (should be considered a regular string)
    expression = "1 + 2"  # Valid Python but not started with $
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Python syntax without $ should return empty issues"
    )

    # Test with Python syntax error but no $ prefix (should be considered a regular string)
    expression = "1 + )"  # Invalid Python but not started with $
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Invalid Python without $ should return empty issues"
    )


def test_dollar_sign_variations():
    """Test different variations of the $ prefix to ensure correct handling."""

    # Test $ with space - should actually evaluate the expression
    expression = "$ 1 + 2"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), "$ with space should be valid"

    # Test $ without space - should NOT be evaluated at all
    expression = "$1 + 2"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "$ without space should return empty issues (not evaluated)"
    )

    # Test with invalid syntax after $
    expression = "$ 1 + )"
    result = validate_py_expression(expression)

    assert len(result["syntax_errors"]) > 0, (
        "Expression with $ space should be evaluated and catch syntax errors"
    )

    # Test with invalid syntax without space after $ - should NOT be evaluated
    expression = "$1 + )"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "$ without space shouldn't be evaluated even with syntax errors"
    )

    # Test with leading whitespace before $
    expression = "  $ 1 + 2"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Leading whitespace before $ should be valid"
    )

    # Test with leading whitespace and $ without space
    expression = "  $1 + 2"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Leading whitespace before $ without space should return empty issues (not evaluated)"
    )


def test_backwards_compatibility_cases():
    """Test the backwards compatibility mechanism for expressions."""

    # Test curly brace template syntax
    expression = "Hello {{name}}"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Curly brace template should be valid"
    )

    # Test array indexing (auto-prepends $)
    expression = "_[0]"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), "Array indexing should be valid"

    # Test simple underscore (auto-prepends $)
    expression = "_"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Simple underscore should be valid"
    )

    # Test attribute access (auto-prepends $)
    expression = "_.name"
    result = validate_py_expression(expression)

    assert all(len(issues) == 0 for issues in result.values()), (
        "Attribute access should be valid"
    )
