import uuid
from unittest.mock import patch

from agents_api.activities.task_steps.base_evaluate import EvaluateError, base_evaluate
from agents_api.autogen.openapi_model import (
    Agent,
    TaskSpecDef,
    ToolCallStep,
    TransitionTarget,
    Workflow,
)
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


@test("utility: base_evaluate - str")
async def _():
    exprs = "$ x + 5"
    values = {"x": 5}
    result = await base_evaluate(exprs, values=values)
    assert result == 10

    exprs = "hello world"
    result = await base_evaluate(exprs, values={})
    assert result == "hello world"


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

    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
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
