import pytest
from agents_api.autogen.openapi_model import CreateTaskRequest
from agents_api.common.utils.task_validation import validate_py_expression, validate_task
from agents_api.env import enable_backwards_compatibility_for_syntax

def test_syntax_error_detection():
    """task_validation: Python expression validator detects syntax errors"""
    expression = '$ 1 + )'
    result = validate_py_expression(expression)
    assert len(result['syntax_errors']) > 0
    assert 'Syntax error' in result['syntax_errors'][0]

def test_undefined_name_detection():
    """task_validation: Python expression validator detects undefined names"""
    expression = '$ undefined_var + 10'
    result = validate_py_expression(expression)
    assert len(result['undefined_names']) > 0
    assert "Undefined name: 'undefined_var'" in result['undefined_names']

def test_allow_steps_var():
    """task_validation: Python expression validator allows steps variable access"""
    expression = '$ steps[0].output'
    result = validate_py_expression(expression)
    assert all((len(issues) == 0 for issues in result.values()))

def test_unsafe_operations_detection():
    """task_validation: Python expression validator detects unsafe operations"""
    expression = '$ some_obj.dangerous_method()'
    result = validate_py_expression(expression)
    assert len(result['unsafe_operations']) > 0
    assert 'Potentially unsafe attribute access' in result['unsafe_operations'][0]

def test_dunder_attribute_detection():
    """task_validation: Python expression validator detects unsafe dunder attributes"""
    expression = '$ obj.__class__'
    result = validate_py_expression(expression)
    assert len(result['unsafe_operations']) > 0
    assert 'Potentially unsafe dunder attribute access: __class__' in result['unsafe_operations'][0]
    expression = "$ obj.__import__('os')"
    result = validate_py_expression(expression)
    assert len(result['unsafe_operations']) > 0
    assert 'Potentially unsafe dunder attribute access: __import__' in result['unsafe_operations'][0]

def test_runtime_error_detection():
    """task_validation: Python expression validator detects potential runtime errors"""
    expression = '$ 10 / 0'
    result = validate_py_expression(expression)
    assert len(result['potential_runtime_errors']) > 0
    assert 'Division by zero' in result['potential_runtime_errors'][0]

def test_backwards_compatibility():
    """task_validation: Python expression backwards_compatibility"""
    if enable_backwards_compatibility_for_syntax:
        expression = '{{ 10 / 0 }}'
        result = validate_py_expression(expression)
        assert len(result['potential_runtime_errors']) > 0
        assert 'Division by zero' in result['potential_runtime_errors'][0]

def test_valid_expression():
    """task_validation: Python expression validator accepts valid expressions"""
    expression = "$ _.topic if hasattr(_, 'topic') else 'default'"
    result = validate_py_expression(expression)
    assert all((len(issues) == 0 for issues in result.values()))

def test_underscore_allowed():
    """task_validation: Python expression validator handles special underscore variable"""
    expression = '$ _.attribute'
    result = validate_py_expression(expression)
    assert all((len(issues) == 0 for issues in result.values()))
invalid_task_dict = {'name': 'Test Task', 'description': 'A task with invalid expressions', 'inherit_tools': True, 'tools': [], 'main': [{'evaluate': {'result': '$ 1 + )'}}, {'if': '$ undefined_var == True', 'then': {'evaluate': {'value': "$ 'valid'"}}}]}
valid_task_dict = {'name': 'Test Task', 'description': 'A task with valid expressions', 'inherit_tools': True, 'tools': [], 'main': [{'evaluate': {'result': '$ 1 + 2'}}, {'if': '$ _ is not None', 'then': {'evaluate': {'value': '$ str(_)'}}}]}

@pytest.mark.skip(reason="CreateTaskRequest model not fully defined - needs investigation")
def test_validation_of_task_with_invalid_expressions():
    """task_validation: Task validator detects invalid Python expressions in tasks"""
    task = CreateTaskRequest.model_validate(invalid_task_dict)
    validation_result = validate_task(task)
    assert not validation_result.is_valid
    assert len(validation_result.python_expression_issues) > 0
    syntax_error_found = False
    undefined_var_found = False
    for issue in validation_result.python_expression_issues:
        if 'Syntax error' in issue.message:
            syntax_error_found = True
        if "Undefined name: 'undefined_var'" in issue.message:
            undefined_var_found = True
    assert syntax_error_found
    assert undefined_var_found

@pytest.mark.skip(reason="CreateTaskRequest model not fully defined - needs investigation")
def test_validation_of_valid_task():
    """task_validation: Task validator accepts valid Python expressions in tasks"""
    task = CreateTaskRequest.model_validate(valid_task_dict)
    validation_result = validate_task(task)
    assert validation_result.is_valid
    assert len(validation_result.python_expression_issues) == 0

@pytest.mark.skip(reason="CreateTaskRequest model not fully defined - needs investigation")
def test_task_validation_simple_test_of_validation_integration():
    """task_validation: Simple test of validation integration"""
    task_dict = {'name': 'Simple Task', 'description': 'A task for basic test', 'inherit_tools': True, 'tools': [], 'main': [{'evaluate': {'result': '$ 1 + 2'}}]}
    task = CreateTaskRequest.model_validate(task_dict)
    validation_result = validate_task(task)
    assert validation_result.is_valid
nested_task_with_error_dict = {'name': 'Nested Error Task', 'description': 'A task with invalid expressions in nested steps', 'inherit_tools': True, 'tools': [], 'main': [{'if': '$ _ is not None', 'then': {'evaluate': {'value': '$ undefined_nested_var'}}, 'else': {'if': '$ True', 'then': {'evaluate': {'result': '$ 1 + )'}}}}, {'match': {'case': '$ _.type', 'cases': [{'case': "$ 'text'", 'then': {'evaluate': {'value': '$ 1 / 0'}}}]}}, {'foreach': {'in': '$ range(3)', 'do': {'evaluate': {'result': '$ unknown_func()'}}}}]}

def test_recursive_validation_of_if_else_branches():
    """Verify that the task validator can identify issues in nested if/else blocks."""
    step_with_nested_if = {'if': {'if': '$ True', 'then': {'evaluate': {'value': '$ 1 + )'}}}}
    task_spec = {'workflows': [{'name': 'main', 'steps': [step_with_nested_if]}]}
    from agents_api.common.utils.task_validation import validate_task_expressions
    validation_results = validate_task_expressions(task_spec)
    assert 'main' in validation_results, 'No validation results for main workflow'
    assert '0' in validation_results['main'], 'No validation results for step 0'
    nested_error_found = False
    for issue in validation_results['main']['0']:
        if 'Syntax error' in str(issue['issues']):
            nested_error_found = True
    assert nested_error_found, 'Did not detect syntax error in nested structure'

def test_recursive_validation_of_match_branches():
    """Verify that the task validator can identify issues in nested match/case blocks."""
    step_with_nested_match = {'match': {'case': '$ _.type', 'cases': [{'case': "$ 'text'", 'then': {'evaluate': {'value': '$ undefined_var'}}}]}}
    task_spec = {'workflows': [{'name': 'main', 'steps': [step_with_nested_match]}]}
    from agents_api.common.utils.task_validation import validate_task_expressions
    validation_results = validate_task_expressions(task_spec)
    nested_error_found = False
    for issue in validation_results['main']['0']:
        if 'undefined_var' in str(issue['expression']) and 'Undefined name' in str(issue['issues']):
            nested_error_found = True
    assert nested_error_found, 'Did not detect undefined variable in nested case structure'

def test_recursive_validation_of_foreach_blocks():
    """Verify that the task validator can identify issues in nested foreach blocks."""
    step_with_nested_foreach = {'foreach': {'in': '$ range(3)', 'do': {'evaluate': {'value': '$ unknown_func()'}}}}
    task_spec = {'workflows': [{'name': 'main', 'steps': [step_with_nested_foreach]}]}
    from agents_api.common.utils.task_validation import validate_task_expressions
    validation_results = validate_task_expressions(task_spec)
    nested_error_found = False
    for issue in validation_results['main']['0']:
        if 'unknown_func()' in str(issue['expression']) and 'Undefined name' in str(issue['issues']):
            nested_error_found = True
    assert nested_error_found, 'Did not detect undefined function in nested foreach structure'

def test_list_comprehension_variables():
    """task_validation: Python expression validator correctly handles list comprehension variables"""
    expression = "$ [item['text'] for item in _['content']]"
    result = validate_py_expression(expression)
    assert all((len(issues) == 0 for issues in result.values())), f'Found issues in valid list comprehension: {result}'

def test_unsupported_features_detection():
    """task_validation: Python expression validator detects unsupported features"""
    expression = '$ {x for x in range(10)}'
    result = validate_py_expression(expression)
    assert len(result['unsupported_features']) > 0
    assert 'Set comprehensions are not supported' in result['unsupported_features'][0]
    expression = '$ (lambda x: x + 1)(5)'
    result = validate_py_expression(expression)
    assert len(result['unsupported_features']) > 0
    assert 'Lambda functions are not supported' in result['unsupported_features'][0]
    expression = '$ (x := 10) + x'
    result = validate_py_expression(expression)
    assert len(result['unsupported_features']) > 0
    assert 'Assignment expressions (walrus operator) are not supported' in result['unsupported_features'][0]