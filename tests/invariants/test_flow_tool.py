from __future__ import annotations

import json
from typing import Any

from julep import dsl
from julep.agent import Tool, tool
from julep.derived import map_n
from julep.dsl import call, native
from julep.typed import Flow, alt, as_flow, par, seq
from julep.ir import Node
from julep.transforms import normalize_ids


def _canonical(node: Node) -> str:
    unshared = Node.from_json(node.to_json())
    return json.dumps(
        normalize_ids(unshared).to_json(), sort_keys=True, separators=(",", ":")
    )


def assert_same_ir(typed: Flow[Any, Any], string_node: Node) -> None:
    assert _canonical(typed.to_ir()) == _canonical(string_node)


def _contains_flow_or_tool(value: Any) -> bool:
    if isinstance(value, (Flow, Tool)):
        return True
    if isinstance(value, dict):
        return any(_contains_flow_or_tool(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_flow_or_tool(item) for item in value)
    return False


def test_tool_leaf_matches_native_call() -> None:
    @tool
    def upper(value: str) -> str:
        return value.upper()

    assert_same_ir(as_flow(upper), call(native(upper.name)))


def test_seq_accepts_tools_and_matches_dsl_seq() -> None:
    @tool
    def first(value: str) -> int:
        return len(value)

    @tool
    def second(value: int) -> str:
        return str(value)

    assert_same_ir(seq(first, second), dsl.seq(call(native(first.name)), call(native(second.name))))


def test_rshift_on_tools_matches_dsl_seq() -> None:
    @tool
    def first(value: str) -> int:
        return len(value)

    @tool
    def second(value: int) -> str:
        return str(value)

    assert_same_ir(first >> second, dsl.seq(call(native(first.name)), call(native(second.name))))


def test_mixed_flow_and_tool_seq_matches_dsl_seq() -> None:
    @tool
    def second(value: str) -> str:
        return value

    a = call(native("a"))

    assert_same_ir(seq(as_flow(a), second), dsl.seq(a, call(native(second.name))))


def test_par_matches_dsl_par_and_reducer_map_n() -> None:
    a = call(native("a"))
    b = call(native("b"))

    assert_same_ir(par([as_flow(a), as_flow(b)]), dsl.par(a, b))
    assert_same_ir(par([as_flow(a), as_flow(b)], join="agg"), map_n(a, b, reducer="agg"))


def test_alt_matches_dsl_alt() -> None:
    a = call(native("a"))
    b = call(native("b"))

    assert_same_ir(alt("pred", as_flow(a), as_flow(b)), dsl.alt("pred", a, b))


def test_flow_and_tool_absent_from_emitted_json() -> None:
    @tool
    def first(value: str) -> int:
        return len(value)

    @tool
    def second(value: int) -> str:
        return str(value)

    encoded_json = seq(first, second).to_ir().to_json()
    encoded = json.dumps(encoded_json)

    assert "Flow" not in encoded
    assert "Tool" not in encoded
    assert not _contains_flow_or_tool(encoded_json)
