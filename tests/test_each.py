"""`each` — dynamic per-item fan-out ([x] -> [y]) — across DSL, validate,
shapes, freeze round-trip, interpreter, plan admission, and approval gating."""

from __future__ import annotations

import pytest

from composable_agents import (
    CapabilityManifest,
    ContextScope,
    Shape,
    blocking,
    call,
    deploy,
    each,
    freeze,
    human_gate,
    mcp,
    register_pure,
    seq,
    think,
    validate,
)
from composable_agents.contracts import McpAnnotations
from composable_agents.errors import ComposableAgentsError
from composable_agents.execution.interpreter import InMemoryEnv, interpret
from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from composable_agents.ir import Node
from composable_agents.kinds import Op
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from composable_agents.shapes import closed_shape, surface_shape
from composable_agents.staged import validate_plan
from composable_agents.transforms import normalize_ids
from conftest import read_snapshot, run

TOOLS = {
    "srv/inc": lambda v: v + 1,
    "srv/double": lambda v: v * 2,
}


def _env(flow, **kw):
    fr, env, _store = _env_and_store(flow, **kw)
    return fr, env


def _env_and_store(flow, **kw):
    fr = freeze(flow, read_snapshot("inc", "double"))
    store = InMemoryProjection()
    return fr, InMemoryEnv(fr.manifest, ProjectionEmitter(store), **kw), store


def _did_attrs(store: InMemoryProjection, node_id: str):
    for e in store.events():
        if e.node == node_id and e.type.value == "Did":
            return e.attrs
    return None


# --------------------------------------------------------------------------- #
# DSL + structure.
# --------------------------------------------------------------------------- #
def test_each_builds_node_with_body_bound_and_reducer():
    n = each(call(mcp("srv", "inc")), max_parallel=3, reducer="each.sum")
    assert n.op == Op.EACH
    assert n.body is not None and n.bound == 3 and n.pure == "each.sum"


def test_each_rejects_bad_max_parallel_at_build():
    with pytest.raises(ValueError):
        each(call(mcp("srv", "inc")), max_parallel=0)


def test_validate_requires_body_and_sane_bound_and_registered_reducer():
    no_body = Node(op=Op.EACH, id="e0")
    assert any(d.code == "EACH_NO_BODY" for d in validate(no_body))

    bad_bound = Node(op=Op.EACH, id="e1", body=call(mcp("srv", "inc")), bound=0)
    assert any(d.code == "EACH_BAD_BOUND" for d in validate(bad_bound))

    unknown = Node(op=Op.EACH, id="e2", body=call(mcp("srv", "inc")), pure="each.nope")
    assert any(d.code == "UNKNOWN_PURE" for d in validate(unknown))

    register_pure("each.known_reducer", lambda xs: xs)
    known = each(call(mcp("srv", "inc")), reducer="each.known_reducer")
    assert not blocking(validate(known))


def test_whole_session_body_warns_degraded():
    flow = each(think("reader", ctx=ContextScope.WHOLE_SESSION))
    diags = validate(flow)
    assert any(d.code == "CTX_EACH_DEGRADED" and d.severity == "warning" for d in diags)


# --------------------------------------------------------------------------- #
# Shape + serialization.
# --------------------------------------------------------------------------- #
def test_each_is_dataflow_and_joins_body_shape():
    plain = each(call(mcp("srv", "inc")))
    assert surface_shape(plain) == Shape.DATAFLOW
    assert closed_shape(plain) == Shape.DATAFLOW


def test_each_round_trips_through_json_and_normalizes_body_path():
    flow = each(call(mcp("srv", "inc")), max_parallel=2, reducer="each.rt")
    back = Node.from_json(flow.to_json())
    assert back.op == Op.EACH and back.bound == 2 and back.pure == "each.rt"
    norm = normalize_ids(Node.from_json(flow.to_json()))
    assert norm.id == "$" and norm.body is not None and norm.body.id == "$.B"


# --------------------------------------------------------------------------- #
# Interpreter semantics.
# --------------------------------------------------------------------------- #
def test_each_maps_body_over_list_in_order():
    fr, env, store = _env_and_store(each(call(mcp("srv", "inc"))), tools=TOOLS)
    out = run(interpret(fr.flow, [1, 2, 3], env))
    assert out.value == [2, 3, 4]
    assert _did_attrs(store, fr.flow.id) == {"items": 3}


def test_each_empty_list_yields_empty_list():
    fr, env = _env(each(call(mcp("srv", "inc"))), tools=TOOLS)
    out = run(interpret(fr.flow, [], env))
    assert out.value == []


def test_each_applies_reducer():
    register_pure("each.sum_all", lambda xs: sum(xs))
    fr, env = _env(each(call(mcp("srv", "inc")), reducer="each.sum_all"), tools=TOOLS)
    out = run(interpret(fr.flow, [1, 2, 3], env))
    assert out.value == 9  # (1+1)+(2+1)+(3+1)


def test_each_rejects_non_list_input():
    fr, env = _env(each(call(mcp("srv", "inc"))), tools=TOOLS)
    with pytest.raises(ComposableAgentsError, match="must be a list"):
        run(interpret(fr.flow, {"not": "a list"}, env))


def test_each_bound_processes_in_waves():
    class CountingEnv(InMemoryEnv):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.wave_sizes: list[int] = []

        async def gather(self, coros):
            self.wave_sizes.append(len(coros))
            return await super().gather(coros)

    fr = freeze(each(call(mcp("srv", "inc")), max_parallel=2), read_snapshot("inc"))
    env = CountingEnv(fr.manifest, ProjectionEmitter(InMemoryProjection()), tools=TOOLS)
    out = run(interpret(fr.flow, [1, 2, 3, 4, 5], env))
    assert out.value == [2, 3, 4, 5, 6]
    assert env.wave_sizes == [2, 2, 1]


def test_each_whole_session_body_runs_sequentially():
    class GatherSpy(InMemoryEnv):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.gathered = False

        async def gather(self, coros):
            self.gathered = True
            return await super().gather(coros)

        async def invoke_reasoner(self, reasoner, value, cid, timeout_s, batchable=False):
            return ("reasoner", value)

    flow = each(think("reader", ctx=ContextScope.WHOLE_SESSION))
    fr = freeze(flow, read_snapshot())
    store = InMemoryProjection()
    env = GatherSpy(fr.manifest, ProjectionEmitter(store))
    out = run(interpret(fr.flow, ["a", "b"], env))
    assert out.value == [("reasoner", "a"), ("reasoner", "b")]
    assert env.gathered is False
    assert _did_attrs(store, fr.flow.id) == {
        "items": 2, "merge": "degraded", "reason": "whole_session",
    }


def test_each_composes_in_seq():
    register_pure("each.flatten_len", lambda xs: len(xs))
    flow = seq(each(call(mcp("srv", "inc"))), Node.from_json(
        {"op": "arr", "id": "len", "pure": "each.flatten_len"}
    ))
    fr, env = _env(flow, tools=TOOLS)
    out = run(interpret(fr.flow, [10, 20], env))
    assert out.value == 2


# --------------------------------------------------------------------------- #
# Staged-plan admission: dynamic fan-out is not admissible.
# --------------------------------------------------------------------------- #
def test_staged_plan_rejects_each():
    plan = each(call(mcp("srv", "inc")))
    diags = validate_plan(plan, CapabilityManifest.from_dict({}))
    assert any(d.code == "PLAN_DYNAMIC_FANOUT" for d in diags)


def test_bodyless_each_plan_is_rejected_cleanly_not_crashed():
    # A model-generated plan can be malformed; shape analysis must return the
    # floor (so admission rejects via diagnostics) rather than raise.
    malformed = Node(op=Op.EACH, id="e3")
    assert surface_shape(malformed) == Shape.DATAFLOW
    assert closed_shape(malformed) == Shape.DATAFLOW
    diags = validate_plan(malformed, CapabilityManifest.from_dict({}))
    codes = {d.code for d in diags}
    assert "EACH_NO_BODY" in codes and "PLAN_DYNAMIC_FANOUT" in codes


# --------------------------------------------------------------------------- #
# Approval gating must see through the each body.
# --------------------------------------------------------------------------- #
def _dangerous_snapshot() -> McpSnapshot:
    dangerous = McpAnnotations(destructive_hint=True)
    return McpSnapshot(servers={
        "srv": McpServerSnapshot(server="srv", version="1", tools={
            "wipe": McpToolSpec(input_schema={}, annotations=dangerous),
        })
    })


def test_approval_required_tool_inside_each_body_is_flagged_without_gate():
    caps = CapabilityManifest.from_dict({"tools": [{"name": "srv/wipe", "approval": True}]})
    ungated = each(call(mcp("srv", "wipe")))
    deployment = deploy(ungated, _dangerous_snapshot(), capabilities=caps, strict=False)
    assert any(d.code == "APPROVAL_UNGATED" for d in blocking(deployment.diagnostics))

    gated = seq(human_gate(), each(call(mcp("srv", "wipe"))))
    deployment = deploy(gated, _dangerous_snapshot(), capabilities=caps, strict=False)
    assert not any(d.code == "APPROVAL_UNGATED" for d in blocking(deployment.diagnostics))
