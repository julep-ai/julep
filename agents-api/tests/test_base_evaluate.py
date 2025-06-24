import uuid
from unittest.mock import patch

import pytest
from agents_api.activities.task_steps.base_evaluate import base_evaluate
from agents_api.autogen.openapi_model import (
    Agent,
    TaskSpecDef,
    ToolCallStep,
    TransitionTarget,
    Workflow,
)
from agents_api.common.exceptions.executions import EvaluateError
from agents_api.common.protocol.tasks import (
    ExecutionInput,
    StepContext,
)
from agents_api.common.utils.datetime import utcnow
from agents_api.common.utils.task_validation import (
    backwards_compatibility,
    validate_py_expression,
)


async def test_base_evaluate_empty_exprs():
    """Test utility: base_evaluate - empty exprs."""
    with pytest.raises(AssertionError):
        await base_evaluate({}, values={"a": 1})


async def test_base_evaluate_value_undefined():
    """Test utility: base_evaluate - value undefined."""
    with pytest.raises(EvaluateError):
        await base_evaluate("$ b", values={"a": 1})


async def test_base_evaluate_scalar_values():
    """Test utility: base_evaluate - scalar values."""
    exprs = [1, 2, True, 1.2459, "$ x + 5"]
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == [1, 2, True, 1.2459, 10]


async def test_base_evaluate_str():
    """Test utility: base_evaluate - str."""
    exprs = "$ x + 5"
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == 10

    # Test with $ but no space - this should NOT be evaluated as Python
    # but treated as a string with an f-string wrapper
    exprs = "$x + 5"
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == "$x + 5", (
        "Expression with $ but no space should be treated as a regular string"
    )

    exprs = "hello world"
    result = await base_evaluate(exprs, values={})
    assert result == "hello world"

    exprs = "I forgot to put a dollar sign, can you still calculate {x + 5}?"
    result = await base_evaluate(exprs, values={"x": 5})
    assert result == "I forgot to put a dollar sign, can you still calculate 10?"


async def test_base_evaluate_dict():
    """Test utility: base_evaluate - dict."""
    exprs = {"a": "$ x + 5", "b": "$ x + 6", "c": "x + 7"}
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == {"a": 10, "b": 11, "c": "x + 7"}


async def test_base_evaluate_list():
    """Test utility: base_evaluate - list."""
    exprs = [{"a": "$ x + 5"}, {"b": "$ x + 6"}, {"c": "x + 7"}]
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == [{"a": 10}, {"b": 11}, {"c": "x + 7"}]


async def test_base_evaluate_parameters():
    """Test utility: base_evaluate - parameters."""
    exprs = "$ x + 5"
    context_none = None
    values_none = None
    extra_lambda_strs_none = None
    step = ToolCallStep(tool="tool1")
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )

    scope_id = uuid.uuid4()
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    values = {"x": 5}
    reduce = "results + [_]"
    reduce = reduce.replace("_", "_item").replace("results", "_result")
    extra_lambda_strs = {"reducer_lambda": f"lambda _result, _item: ({reduce})"}

    with patch(
        "agents_api.common.protocol.tasks.StepContext.prepare_for_step",
        return_value={"x": 10},
    ):
        with pytest.raises(ValueError):
            result = await base_evaluate(
                exprs,
                context=context_none,
                values=values_none,
                extra_lambda_strs=extra_lambda_strs_none,
            )
        with pytest.raises(ValueError):
            result = await base_evaluate(
                exprs,
                context=context_none,
                values=values_none,
                extra_lambda_strs=extra_lambda_strs,
            )
        result = await base_evaluate(
            exprs,
            context=context_none,
            values=values,
            extra_lambda_strs=extra_lambda_strs_none,
        )
        assert result == 10
        result = await base_evaluate(
            exprs,
            context=context_none,
            values=values,
            extra_lambda_strs=extra_lambda_strs,
        )
        assert result == 10
        result = await base_evaluate(
            exprs,
            context=context,
            values=values_none,
            extra_lambda_strs=extra_lambda_strs_none,
        )
        assert result == 15
        result = await base_evaluate(
            exprs,
            context=context,
            values=values_none,
            extra_lambda_strs=extra_lambda_strs,
        )
        assert result == 15
        result = await base_evaluate(
            exprs,
            context=context,
            values=values,
            extra_lambda_strs=extra_lambda_strs_none,
        )
        assert result == 15
        result = await base_evaluate(
            exprs,
            context=context,
            values=values,
            extra_lambda_strs=extra_lambda_strs,
        )
        assert result == 15


async def test_base_evaluate_backwards_compatibility():
    """Test utility: base_evaluate - backwards compatibility."""
    exprs = "[[x + 5]]"
    values = {"x": 5, "inputs": {1: 1}, "outputs": {1: 2}}
    result = await base_evaluate(exprs, values=values)
    assert result == [[10]]

    # Test inputs[] and outputs[] access
    exprs = "inputs[1]"
    result = await base_evaluate(exprs, values=values)
    assert result == 1

    exprs = "outputs[1]"
    result = await base_evaluate(exprs, values=values)
    assert result == 2

    # Test template expressions
    exprs = "Value is {{x}}"
    result = await base_evaluate(exprs, values=values)
    assert result == "Value is 5"

    # Test underscore expressions
    exprs = "_"
    result = await base_evaluate(exprs, values={"_": 42})
    assert result == 42

    exprs = "_.field[0]"
    result = await base_evaluate(exprs, values={"_": {"field": [10]}})
    assert result == 10

    exprs = "_[0]"
    result = await base_evaluate(exprs, values={"_": [7]})
    assert result == 7


async def test_backwards_compatibility():
    """Test utility: backwards_compatibility."""
    # Test $ prefix - should return unchanged
    exprs = "$ x + 5"
    result = backwards_compatibility(exprs)
    assert result == "$ x + 5"

    # Test template expressions
    exprs = "{{x + 5}}"
    result = backwards_compatibility(exprs)
    assert result == "$ f'''{x + 5}'''"

    exprs = "Value is {{x}} and {{y}}"
    result = backwards_compatibility(exprs)
    assert result == "$ f'''Value is {x} and {y}'''"

    # Test bracket expressions
    exprs = "[x + 5]"
    result = backwards_compatibility(exprs)
    assert result == "$ [x + 5]"

    exprs = "[[nested]]"
    result = backwards_compatibility(exprs)
    assert result == "$ [[nested]]"

    # Test underscore expressions
    exprs = "_[0]"
    result = backwards_compatibility(exprs)
    assert result == "$ _[0]"

    exprs = "_.field[0]"
    result = backwards_compatibility(exprs)
    assert result == "$ _.field[0]"

    exprs = "_"
    result = backwards_compatibility(exprs)
    assert result == "$ _"

    # Test inputs/outputs access
    exprs = "input for input in inputs[key]"
    result = backwards_compatibility(exprs)
    assert result == "$ input for input in inputs[key]"

    exprs = "output for output in outputs[key]"
    result = backwards_compatibility(exprs)
    assert result == "$ output for output in outputs[key]"

    # Test plain string - should return unchanged
    exprs = "hello world"
    result = backwards_compatibility(exprs)
    assert result == "hello world"

    # Test spaces at the beginning and end
    exprs = "  _[0]  "
    result = backwards_compatibility(exprs)
    assert result == "$ _[0]"


def test_validate_non_dollar_expressions():
    """Tests that expressions without $ prefix return empty issues and don't get validated."""
    # Regular string without $ prefix
    expression = "Hello world"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())

    # Valid Python syntax but no $ prefix
    expression = "1 + 2"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())

    # Invalid Python syntax but no $ prefix
    expression = "1 + )"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())


def test_dollar_sign_prefix_formats():
    """Tests that $ prefix is correctly recognized in various formats."""
    # $ with space
    expression = "$ 1 + 2"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())

    # $ without space
    expression = "$1 + 2"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())

    # Leading whitespace before $
    expression = "   $ 1 + 2"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())

    # Leading whitespace and $ without space
    expression = "   $1 + 2"
    result = validate_py_expression(expression)
    assert all(len(issues) == 0 for issues in result.values())


def test_validate_edge_cases():
    """Tests edge cases like empty strings, None values, etc."""
    # None value
    result = validate_py_expression(None)
    assert all(len(issues) == 0 for issues in result.values())

    # Empty string
    result = validate_py_expression("")
    assert all(len(issues) == 0 for issues in result.values())

    # Just whitespace
    result = validate_py_expression("   ")
    assert all(len(issues) == 0 for issues in result.values())

    # Just $ sign
    result = validate_py_expression("$")
    assert all(len(issues) == 0 for issues in result.values())
