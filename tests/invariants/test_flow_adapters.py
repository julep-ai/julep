import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # mypy targets 3.10 (no typing.assert_type); runtime may be 3.10 too
    from typing_extensions import assert_type
else:
    try:
        from typing import assert_type
    except ImportError:  # Python 3.10: assert_type is a static-only helper; no-op at runtime

        def assert_type(val, typ, /):
            return val

from composable_agents import dsl
from composable_agents.dsl import native
from composable_agents.flow import Flow, as_flow
from composable_agents.flow_adapters import AnyEdge, any_edges, as_type, expect
from composable_agents.ir import Node
from composable_agents.kinds import Op
from composable_agents.transforms import normalize_ids


def _canonical(node: Node) -> str:
    unshared = Node.from_json(node.to_json())
    return json.dumps(
        normalize_ids(unshared).to_json(), sort_keys=True, separators=(",", ":")
    )


def _no_id(j: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in j.items() if k != "id"}


def test_as_type_lowers_to_ident() -> None:
    assert as_type(int).to_ir().op is Op.IDENT
    assert _no_id(as_type(int).to_ir().to_json()) == _no_id(dsl.ident().to_json())
    assert _canonical(as_type(int).to_ir()) == _canonical(dsl.ident())


def test_as_type_threads_types() -> None:
    base = as_flow(dsl.call(native("x"))) >> as_type(int)
    assert_type(base, Flow[Any, int])
    leaf: Flow[int, str] = as_flow(dsl.call(native("y")))
    chained = base >> leaf
    assert_type(chained, Flow[Any, str])
    assert isinstance(chained, Flow)


def test_expect_retypes_output() -> None:
    base = as_flow(dsl.app("agent"))
    typed = expect(base, int)
    assert_type(typed, Flow[Any, int])
    assert isinstance(typed, Flow)


def test_expect_ir_is_f_then_ident() -> None:
    a = dsl.call(native("x"))
    assert _canonical(expect(as_flow(a), int).to_ir()) == _canonical(
        dsl.seq(a, dsl.ident())
    )


def test_any_edges_flags_app() -> None:
    edges = any_edges(as_flow(dsl.app("agent")))
    assert len(edges) == 1
    assert edges[0].op == "app"
    assert isinstance(edges[0], AnyEdge)


def test_any_edges_flags_think() -> None:
    edges = any_edges(as_flow(dsl.think("brain")))
    assert [e.op for e in edges] == ["prim"]
    assert "think" in edges[0].reason


def test_any_edges_omits_typed_pipeline() -> None:
    pipe = as_flow(dsl.call(native("x"))) >> as_flow(dsl.call(native("y")))
    assert any_edges(pipe) == []


def test_as_type_ident_not_flagged() -> None:
    assert any_edges(as_type(int)) == []
