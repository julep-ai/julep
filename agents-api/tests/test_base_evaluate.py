import uuid
from unittest.mock import patch

from agents_api.activities.task_steps.base_evaluate import (
    backwards_compatibility,
    base_evaluate,
)
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
from ward import raises, test


@test("utility: base_evaluate - empty exprs")
async def _():
    with raises(AssertionError):
        await base_evaluate({}, values={"a": 1})


@test("utility: base_evaluate - value undefined")
async def _():
    with raises(EvaluateError):
        await base_evaluate("$ b", values={"a": 1})


@test("utility: base_evaluate - scalar values")
async def _():
    exprs = [1, 2, True, 1.2459, "$ x + 5"]
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == [1, 2, True, 1.2459, 10]


@test("utility: base_evaluate - str")
async def _():
    exprs = "$ x + 5"
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == 10

    exprs = "hello world"
    result = await base_evaluate(exprs, values={})
    assert result == "hello world"

    exprs = "I forgot to put a dollar sign, can you still calculate {x + 5}?"
    result = await base_evaluate(exprs, values={"x": 5})
    assert result == "I forgot to put a dollar sign, can you still calculate 10?"


@test("utility: base_evaluate - dict")
async def _():
    exprs = {"a": "$ x + 5", "b": "$ x + 6", "c": "x + 7"}
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == {"a": 10, "b": 11, "c": "x + 7"}


@test("utility: base_evaluate - list")
async def _():
    exprs = [{"a": "$ x + 5"}, {"b": "$ x + 6"}, {"c": "x + 7"}]
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == [{"a": 10}, {"b": 11}, {"c": "x + 7"}]


@test("utility: base_evaluate - parameters")
async def _():
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
        "agents_api.common.protocol.tasks.StepContext.prepare_for_step", return_value={"x": 10}
    ):
        with raises(ValueError):
            result = await base_evaluate(
                exprs,
                context=context_none,
                values=values_none,
                extra_lambda_strs=extra_lambda_strs_none,
            )
        with raises(ValueError):
            result = await base_evaluate(
                exprs,
                context=context_none,
                values=values_none,
                extra_lambda_strs=extra_lambda_strs,
            )
        result = await base_evaluate(
            exprs, context=context_none, values=values, extra_lambda_strs=extra_lambda_strs_none
        )
        assert result == 10
        result = await base_evaluate(
            exprs, context=context_none, values=values, extra_lambda_strs=extra_lambda_strs
        )
        assert result == 10
        result = await base_evaluate(
            exprs, context=context, values=values_none, extra_lambda_strs=extra_lambda_strs_none
        )
        assert result == 15
        result = await base_evaluate(
            exprs, context=context, values=values_none, extra_lambda_strs=extra_lambda_strs
        )
        assert result == 15
        result = await base_evaluate(
            exprs, context=context, values=values, extra_lambda_strs=extra_lambda_strs_none
        )
        assert result == 15
        result = await base_evaluate(
            exprs, context=context, values=values, extra_lambda_strs=extra_lambda_strs
        )
        assert result == 15


@test("utility: base_evaluate - backwards compatibility")
async def _():
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


@test("utility: backwards_compatibility")
async def _():
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
