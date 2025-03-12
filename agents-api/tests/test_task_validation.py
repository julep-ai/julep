from agents_api.activities.task_steps.base_evaluate import validate_py_expression
from agents_api.autogen.openapi_model import CreateTaskRequest
from agents_api.common.utils.task_validation import validate_task
from ward import fixture, test


@test("Python expression validator detects syntax errors")
def test_syntax_error_detection():
    # Test with a syntax error
    expression = "$ 1 + )"
    result = validate_py_expression(expression)
    assert len(result["syntax_errors"]) > 0
    assert "Syntax error" in result["syntax_errors"][0]


@test("Python expression validator detects undefined names")
def test_undefined_name_detection():
    # Test with undefined variable
    expression = "$ undefined_var + 10"
    result = validate_py_expression(expression)
    assert len(result["undefined_names"]) > 0
    assert "Undefined name: 'undefined_var'" in result["undefined_names"]


@test("Python expression validator detects unsafe operations")
def test_unsafe_operations_detection():
    # Test with unsafe attribute access
    expression = "$ some_obj.dangerous_method()"
    result = validate_py_expression(expression)
    assert len(result["unsafe_operations"]) > 0
    assert "Potentially unsafe attribute access" in result["unsafe_operations"][0]


@test("Python expression validator detects potential runtime errors")
def test_runtime_error_detection():
    # Test division by zero
    expression = "$ 10 / 0"
    result = validate_py_expression(expression)
    assert len(result["potential_runtime_errors"]) > 0
    assert "Division by zero" in result["potential_runtime_errors"][0]


@test("Python expression validator accepts valid expressions")
def test_valid_expression():
    # Test a valid expression
    expression = "$ _.topic if hasattr(_, 'topic') else 'default'"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())


@test("Python expression validator handles special underscore variable")
def test_underscore_allowed():
    # Test that _ is allowed by default
    expression = "$ _.attribute"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())

    # Test that _ is not allowed when allow_placeholder_variables is False
    result = validate_py_expression(expression, allow_placeholder_variables=False)
    assert len(result["undefined_names"]) > 0


@fixture
def invalid_task_dict():
    return {
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


@fixture
def valid_task_dict():
    return {
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


@test("Task validator detects invalid Python expressions in tasks")
def test_validation_of_task_with_invalid_expressions(invalid_task_dict=invalid_task_dict):
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


@test("Task validator accepts valid Python expressions in tasks")
def test_validation_of_valid_task(valid_task_dict=valid_task_dict):
    # Convert dict to CreateTaskRequest
    task = CreateTaskRequest.model_validate(valid_task_dict)

    # Validate the task
    validation_result = validate_task(task)

    # Verify validation result
    assert validation_result.is_valid
    assert len(validation_result.python_expression_issues) == 0


@test("Simple test of validation integration")
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
