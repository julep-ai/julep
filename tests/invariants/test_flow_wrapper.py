import json
from typing import Any

from composable_agents import dsl
from composable_agents.dsl import call, mcp, native
from composable_agents.flow import Flow, flow, seq
from composable_agents.ir import Node
from composable_agents.transforms import normalize_ids


def _canonical(node: Node) -> str:
    # Unshare via a JSON round-trip (freeze step 2), then normalize ids to
    # deterministic position paths (freeze step 3). What remains is the semantic IR.
    unshared = Node.from_json(node.to_json())
    return json.dumps(
        normalize_ids(unshared).to_json(), sort_keys=True, separators=(",", ":")
    )


def assert_same_ir(typed: Flow[object, object], string_node: Node) -> None:
    assert _canonical(typed.to_ir()) == _canonical(string_node)


def _contains_flow(value: Any) -> bool:
    if isinstance(value, Flow):
        return True
    if isinstance(value, dict):
        return any(_contains_flow(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_flow(item) for item in value)
    return False


def test_seq_two_matches_dsl_seq() -> None:
    a = call(native("x"))
    b = call(mcp("s", "t"))

    assert_same_ir(seq(flow(a), flow(b)), dsl.seq(a, b))


def test_rshift_chain_matches_dsl_seq() -> None:
    a = call(native("x"))
    b = call(mcp("s", "t"))
    c = call(native("z"))

    assert_same_ir(flow(a) >> flow(b) >> flow(c), dsl.seq(a, b, c))


def test_single_element_seq() -> None:
    a = call(native("x"))

    assert_same_ir(seq(flow(a)), a)


def test_nested_composition() -> None:
    a = call(native("a"))
    b = call(mcp("s", "b"))
    c = call(native("c"))
    d = call(mcp("s", "d"))

    composed = seq(flow(a), flow(b)) >> seq(flow(c), flow(d))

    assert_same_ir(composed, dsl.seq(dsl.seq(a, b), dsl.seq(c, d)))


def test_flow_absent_from_emitted_json() -> None:
    a = call(native("x"))
    b = call(mcp("s", "t"))
    node = seq(flow(a), flow(b)).to_ir()

    j = node.to_json()
    encoded = json.dumps(j)

    assert "Flow" not in encoded
    assert not _contains_flow(j)
