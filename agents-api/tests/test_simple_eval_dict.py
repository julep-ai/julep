from agents_api.activities.utils import MAX_COLLECTION_SIZE, MAX_STRING_LENGTH, simple_eval_dict
from simpleeval import NameNotDefined
from ward import raises, test


@test("utility: simple_eval_dict - string length overflow")
async def _():
    with raises(ValueError):
        simple_eval_dict({"a": "b" * (MAX_STRING_LENGTH + 1)}, {})


@test("utility: simple_eval_dict - collection size overflow")
async def _():
    with raises(ValueError):
        simple_eval_dict({str(i): "b" for i in range(MAX_COLLECTION_SIZE + 1)}, {})


@test("utility: simple_eval_dict - value undefined")
async def _():
    with raises(NameNotDefined):
        simple_eval_dict({"a": "b"}, {})


@test("utility: simple_eval_dict")
async def _():
    exprs = {"a": {"b": "x + 5", "c": "x + 6"}}
    values = {"x": 5}
    result = simple_eval_dict(exprs, values)
    assert result == {"a": {"b": 10, "c": 11}}
