"""
Simple tests to verify that our Python expression validation works.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents_api.activities.task_steps.base_evaluate import validate_py_expression


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
    
    # Test division by zero detection
    expression = "$ 10 / 0"
    result = validate_py_expression(expression)
    assert len(result["potential_runtime_errors"]) > 0
    assert "Division by zero" in result["potential_runtime_errors"][0]
    
    # Test a valid expression
    expression = "$ _.topic if hasattr(_, 'topic') else 'default'"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())

    # Test that _ is allowed by default
    expression = "$ _.attribute"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())
    
    # Test that _ is not allowed when allow_placeholder_variables is False
    result = validate_py_expression(expression, allow_placeholder_variables=False)
    assert len(result["undefined_names"]) > 0


if __name__ == "__main__":
    test_expression_validation_basic()
    print("All tests passed!")