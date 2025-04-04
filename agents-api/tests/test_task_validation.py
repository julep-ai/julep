from agents_api.autogen.openapi_model import CreateTaskRequest
from agents_api.common.utils.task_validation import validate_py_expression, validate_task
from agents_api.env import enable_backwards_compatibility_for_syntax
from ward import test


@test("task_validation: Python expression validator detects syntax errors")
def test_syntax_error_detection():
    # Test with a syntax error
    expression = "$ 1 + )"
    result = validate_py_expression(expression)
    assert len(result["syntax_errors"]) > 0
    assert "Syntax error" in result["syntax_errors"][0]


@test("task_validation: Python expression validator detects undefined names")
def test_undefined_name_detection():
    # Test with undefined variable
    expression = "$ undefined_var + 10"
    result = validate_py_expression(expression)
    assert len(result["undefined_names"]) > 0
    assert "Undefined name: 'undefined_var'" in result["undefined_names"]


@test("task_validation: Python expression validator allows steps variable access")
def test_allow_steps_var():
    # Test with accessing steps
    expression = "$ steps[0].output"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())


@test("task_validation: Python expression validator detects unsafe operations")
def test_unsafe_operations_detection():
    # Test with unsafe attribute access
    expression = "$ some_obj.dangerous_method()"
    result = validate_py_expression(expression)
    assert len(result["unsafe_operations"]) > 0
    assert "Potentially unsafe attribute access" in result["unsafe_operations"][0]


@test("task_validation: Python expression validator detects unsafe dunder attributes")
def test_dunder_attribute_detection():
    # Test with dangerous dunder attribute access
    expression = "$ obj.__class__"
    result = validate_py_expression(expression)
    assert len(result["unsafe_operations"]) > 0
    assert (
        "Potentially unsafe dunder attribute access: __class__"
        in result["unsafe_operations"][0]
    )

    # Test with another dangerous dunder attribute
    expression = "$ obj.__import__('os')"
    result = validate_py_expression(expression)
    assert len(result["unsafe_operations"]) > 0
    assert (
        "Potentially unsafe dunder attribute access: __import__"
        in result["unsafe_operations"][0]
    )


@test("task_validation: Python expression validator detects potential runtime errors")
def test_runtime_error_detection():
    # Test division by zero
    expression = "$ 10 / 0"
    result = validate_py_expression(expression)
    assert len(result["potential_runtime_errors"]) > 0
    assert "Division by zero" in result["potential_runtime_errors"][0]


@test("task_validation: Python expression backwards_compatibility")
def test_backwards_compatibility():
    if enable_backwards_compatibility_for_syntax:
        # Test division by zero
        expression = "{{ 10 / 0 }}"
        result = validate_py_expression(expression)
        assert len(result["potential_runtime_errors"]) > 0
        assert "Division by zero" in result["potential_runtime_errors"][0]


@test("task_validation: Python expression validator accepts valid expressions")
def test_valid_expression():
    # Test a valid expression
    expression = "$ _.topic if hasattr(_, 'topic') else 'default'"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())


@test("task_validation: Python expression validator handles special underscore variable")
def test_underscore_allowed():
    # Test that _ is allowed by default
    expression = "$ _.attribute"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())


invalid_task_dict = {
    "name": "Test Task",
    "description": "A task with invalid expressions",
    "inherit_tools": True,
    "tools": [],
    "main": [
        {
            "evaluate": {
                "result": "$ 1 + )"  # Syntax error
            }
        },
        {
            "if": "$ undefined_var == True",  # Undefined variable
            "then": {"evaluate": {"value": "$ 'valid'"}},
        },
    ],
}


valid_task_dict = {
    "name": "Test Task",
    "description": "A task with valid expressions",
    "inherit_tools": True,
    "tools": [],
    "main": [
        {
            "evaluate": {
                "result": "$ 1 + 2"  # Valid expression
            }
        },
        {
            "if": "$ _ is not None",  # Valid expression
            "then": {"evaluate": {"value": "$ str(_)"}},
        },
    ],
}


@test("task_validation: Task validator detects invalid Python expressions in tasks")
def test_validation_of_task_with_invalid_expressions():
    # Convert dict to CreateTaskRequest
    task = CreateTaskRequest.model_validate(invalid_task_dict)

    # Validate the task
    validation_result = validate_task(task)

    # Verify validation result
    assert not validation_result.is_valid
    assert len(validation_result.python_expression_issues) > 0

    # Check that both issues were detected
    syntax_error_found = False
    undefined_var_found = False

    for issue in validation_result.python_expression_issues:
        if "Syntax error" in issue.message:
            syntax_error_found = True
        if "Undefined name: 'undefined_var'" in issue.message:
            undefined_var_found = True

    assert syntax_error_found
    assert undefined_var_found


@test("task_validation: Task validator accepts valid Python expressions in tasks")
def test_validation_of_valid_task():
    # Convert dict to CreateTaskRequest
    task = CreateTaskRequest.model_validate(valid_task_dict)

    # Validate the task
    validation_result = validate_task(task)

    # Verify validation result
    assert validation_result.is_valid
    assert len(validation_result.python_expression_issues) == 0


@test("task_validation: Simple test of validation integration")
def _():
    # Create a simple valid task
    task_dict = {
        "name": "Simple Task",
        "description": "A task for basic test",
        "inherit_tools": True,
        "tools": [],
        "main": [{"evaluate": {"result": "$ 1 + 2"}}],
    }

    task = CreateTaskRequest.model_validate(task_dict)

    # Validate the task with the actual validator
    validation_result = validate_task(task)

    # Should be valid since the expression is correct
    assert validation_result.is_valid


nested_task_with_error_dict = {
    "name": "Nested Error Task",
    "description": "A task with invalid expressions in nested steps",
    "inherit_tools": True,
    "tools": [],
    "main": [
        {
            "if": "$ _ is not None",  # Valid expression
            "then": {
                "evaluate": {
                    "value": "$ undefined_nested_var"  # Invalid: undefined variable
                }
            },
            "else": {
                "if": "$ True",
                "then": {
                    "evaluate": {
                        "result": "$ 1 + )"  # Invalid: syntax error
                    }
                },
            },
        },
        {
            "match": {
                "case": "$ _.type",
                "cases": [
                    {
                        "case": "$ 'text'",
                        "then": {
                            "evaluate": {
                                "value": "$ 1 / 0"  # Invalid: division by zero
                            }
                        },
                    }
                ],
            }
        },
        {
            "foreach": {
                "in": "$ range(3)",
                "do": {
                    "evaluate": {
                        "result": "$ unknown_func()"  # Invalid: undefined function
                    }
                },
            }
        },
    ],
}


@test("task_validation: Task validator can identify issues in if/else nested branches")
def test_recursive_validation_of_if_else_branches():
    """Verify that the task validator can identify issues in nested if/else blocks."""
    # Manually set up an if step with a nested step structure
    step_with_nested_if = {
        "if": {  # Note: Using this format for Pydantic validation
            "if": "$ True",  # Valid expression
            "then": {
                "evaluate": {
                    "value": "$ 1 + )"  # Deliberate syntax error in nested step
                }
            },
        }
    }

    # Convert to task spec format
    task_spec = {"workflows": [{"name": "main", "steps": [step_with_nested_if]}]}

    # Check task validation using the full validator
    from agents_api.common.utils.task_validation import validate_task_expressions

    validation_results = validate_task_expressions(task_spec)

    # Check that we found the issue in the nested structure
    assert "main" in validation_results, "No validation results for main workflow"
    assert "0" in validation_results["main"], "No validation results for step 0"

    # Check specifically for syntax error in a nested structure
    nested_error_found = False
    for issue in validation_results["main"]["0"]:
        if "Syntax error" in str(issue["issues"]):
            nested_error_found = True

    assert nested_error_found, "Did not detect syntax error in nested structure"


@test("task_validation: Task validator can identify issues in match statement nested blocks")
def test_recursive_validation_of_match_branches():
    """Verify that the task validator can identify issues in nested match/case blocks."""
    # Set up a match step with a nested error
    step_with_nested_match = {
        "match": {
            "case": "$ _.type",
            "cases": [
                {
                    "case": "$ 'text'",
                    "then": {
                        "evaluate": {
                            "value": "$ undefined_var"  # Deliberate undefined variable
                        }
                    },
                }
            ],
        }
    }

    # Convert to task spec format
    task_spec = {"workflows": [{"name": "main", "steps": [step_with_nested_match]}]}

    # Check task validation using the full validator
    from agents_api.common.utils.task_validation import validate_task_expressions

    validation_results = validate_task_expressions(task_spec)

    # Check that we found the issue in the nested structure
    nested_error_found = False
    for issue in validation_results["main"]["0"]:
        if "undefined_var" in str(issue["expression"]) and "Undefined name" in str(
            issue["issues"]
        ):
            nested_error_found = True

    assert nested_error_found, "Did not detect undefined variable in nested case structure"


@test("task_validation: Task validator can identify issues in foreach nested blocks")
def test_recursive_validation_of_foreach_blocks():
    """Verify that the task validator can identify issues in nested foreach blocks."""
    # Set up a foreach step with a nested error
    step_with_nested_foreach = {
        "foreach": {
            "in": "$ range(3)",
            "do": {
                "evaluate": {
                    "value": "$ unknown_func()"  # Deliberate undefined function
                }
            },
        }
    }

    # Convert to task spec format
    task_spec = {"workflows": [{"name": "main", "steps": [step_with_nested_foreach]}]}

    # Check task validation using the full validator
    from agents_api.common.utils.task_validation import validate_task_expressions

    validation_results = validate_task_expressions(task_spec)

    # Check that we found the issue in the nested structure
    nested_error_found = False
    for issue in validation_results["main"]["0"]:
        if "unknown_func()" in str(issue["expression"]) and "Undefined name" in str(
            issue["issues"]
        ):
            nested_error_found = True

    assert nested_error_found, "Did not detect undefined function in nested foreach structure"


@test(
    "task_validation: Python expression validator correctly handles list comprehension variables"
)
def test_list_comprehension_variables():
    # Test with a list comprehension that uses a local variable
    expression = "$ [item['text'] for item in _['content']]"
    result = validate_py_expression(expression)

    # Should not have any undefined name issues for 'item'
    assert all(len(issues) == 0 for issues in result.values()), (
        f"Found issues in valid list comprehension: {result}"
    )


@test("task_validation: Python expression validator detects unsupported features")
def test_unsupported_features_detection():
    # Test with a set comprehension (unsupported)
    expression = "$ {x for x in range(10)}"
    result = validate_py_expression(expression)

    # Should detect the set comprehension as unsupported
    assert len(result["unsupported_features"]) > 0
    assert "Set comprehensions are not supported" in result["unsupported_features"][0]

    # Test with a lambda function (unsupported)
    expression = "$ (lambda x: x + 1)(5)"
    result = validate_py_expression(expression)

    # Should detect the lambda function as unsupported
    assert len(result["unsupported_features"]) > 0
    assert "Lambda functions are not supported" in result["unsupported_features"][0]

    # Test with a walrus operator (unsupported)
    expression = "$ (x := 10) + x"
    result = validate_py_expression(expression)

    # Should detect the walrus operator as unsupported
    assert len(result["unsupported_features"]) > 0
    assert (
        "Assignment expressions (walrus operator) are not supported"
        in result["unsupported_features"][0]
    )
