from __future__ import annotations

from composable_agents.agent import tool


def test_multiarg_tool_uses_object_schema_and_bound_tool_packs_kwargs() -> None:
    @tool
    def book(hotel: str, nights: int) -> str:
        return f"{hotel}:{nights}"

    assert book.input_schema == {
        "type": "object",
        "properties": {
            "hotel": {"type": "string"},
            "nights": {"type": "integer"},
        },
        "required": ["hotel", "nights"],
        "additionalProperties": False,
    }
    assert book.bound_tool({"hotel": "x", "nights": 3}) == "x:3"
    assert book("x", 3) == "x:3"


def test_single_arg_tool_schema_and_bound_tool_are_unchanged() -> None:
    @tool
    def s(q: str) -> int:
        return len(q)

    assert s.input_schema == {"type": "string"}
    assert s.bound_tool is s.fn
    assert s.bound_tool("hi") == 2


def test_positional_only_multiarg_tool_packs_positionally() -> None:
    @tool
    def book(hotel: str, nights: int, /) -> str:
        return f"{hotel}:{nights}"

    assert book.input_schema["type"] == "object"
    assert book.bound_tool({"hotel": "x", "nights": 3}) == "x:3"
    assert book("x", 3) == "x:3"


def test_mixed_positional_only_and_keyword_multiarg_tool() -> None:
    @tool
    def f(a: str, /, b: int) -> str:
        return f"{a}:{b}"

    assert f.bound_tool({"a": "x", "b": 2}) == "x:2"
    assert f("x", 2) == "x:2"
