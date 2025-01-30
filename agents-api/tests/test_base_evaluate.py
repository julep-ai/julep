from agents_api.activities.task_steps.base_evaluate import EvaluateError, base_evaluate
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
