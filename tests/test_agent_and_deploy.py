"""Pure agent-loop (P4) and deploy-pipeline tests (no Temporal)."""

from __future__ import annotations

import pytest

import composable_agents
from composable_agents import (
    AgentConfig, AgentState, Decision, interpret_brain_reply,
    generalize_trace_to_plan, extract_plan, promote_plan,
    CapabilityManifest, Budget, Brain,
    deploy, snapshot_from_listings,
    alt, app, arr, call, iter_up_to, mcp, par, seq, stage, think,
)
from composable_agents import dotctx, purity
from composable_agents.agent_loop import (
    TraceEntry, action_cost, would_exceed_budget, should_continue_as_new,
    terminal_result, RoundAction,
)
from composable_agents.ir import Merge
from composable_agents.purity import PureEntry
from composable_agents.errors import PlanRejected, ValidationError
from composable_agents.derived import race
from conftest import read_snapshot, mixed_snapshot


# --------------------------------------------------------------------------- #
# Brain reply interpretation (the closed action vocabulary).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("reply,decision", [
    ({"done": True, "output": 42}, Decision.FINISH),
    ({"output": "ans"}, Decision.FINISH),
    ({"tool": "search", "input": {"q": "x"}}, Decision.CALL),
    ({"sub": "child", "input": 1}, Decision.SUB),
    ({"escalate": "stuck"}, Decision.ESCALATE),
    ("just prose", Decision.FINISH),
    ({"unknown": "shape"}, Decision.FINISH),
])
def test_interpret_brain_reply_maps_vocabulary(reply, decision):
    assert interpret_brain_reply(reply).decision is decision


def test_terminal_actions_flagged():
    assert RoundAction(Decision.FINISH).is_terminal
    assert RoundAction(Decision.ESCALATE).is_terminal
    assert not RoundAction(Decision.CALL).is_terminal


def test_action_cost_defaults():
    assert action_cost(RoundAction(Decision.CALL)) == 1.0
    assert action_cost(RoundAction(Decision.SUB)) == 5.0
    assert action_cost(RoundAction(Decision.CALL), reported=0.25) == 0.25


# --------------------------------------------------------------------------- #
# State + budget + continue-as-new (continue-as-new safety = JSON round-trip).
# --------------------------------------------------------------------------- #
def test_state_json_round_trip():
    s = AgentState(round=3, spent_usd=7.5, last={"k": 1})
    s.record(TraceEntry(decision="call", ref="search", cost=1.0))
    s.record(TraceEntry(decision="sub", ref="child", shape="Pipeline", cost=5.0))
    s2 = AgentState.from_json(s.to_json())
    assert s2.round == 3 and s2.spent_usd == 7.5
    assert [t.ref for t in s2.trace] == ["search", "child"]


def test_config_json_round_trip():
    c = AgentConfig(max_rounds=10, budget=Budget(usd=3.0, tokens=1000), continue_as_new_after=4)
    c2 = AgentConfig.from_json(c.to_json())
    assert c2.max_rounds == 10 and c2.budget.usd == 3.0 and c2.continue_as_new_after == 4


def test_budget_guard():
    b = Budget(usd=10.0)
    assert would_exceed_budget(AgentState(spent_usd=8.0), 5.0, b) is True
    assert would_exceed_budget(AgentState(spent_usd=8.0), 1.0, b) is False
    assert would_exceed_budget(AgentState(spent_usd=8.0), 5.0, None) is False


def test_continue_as_new_policy():
    cfg = AgentConfig(continue_as_new_after=5)
    assert should_continue_as_new(AgentState(round=5), cfg) is True
    assert should_continue_as_new(AgentState(round=4), cfg) is False
    assert should_continue_as_new(AgentState(round=99), AgentConfig(continue_as_new_after=0)) is False


def test_config_from_capabilities_inherits_budget():
    caps = CapabilityManifest.from_dict({"budget": {"usd": 12.0}})
    cfg = AgentConfig.from_capabilities(caps, max_rounds=7)
    assert cfg.budget.usd == 12.0 and cfg.max_rounds == 7


def test_terminal_result_shape():
    s = AgentState(round=2, spent_usd=3.0, last="x")
    r = terminal_result("done", s, output="final")
    assert r["status"] == "done" and r["output"] == "final" and r["rounds"] == 2


# --------------------------------------------------------------------------- #
# Plan extraction + promotion (offline generalization of a trace).
# --------------------------------------------------------------------------- #
def test_generalize_trace_to_plan_chains_calls_and_subs():
    trace = [
        TraceEntry(decision="call", ref="search"),
        TraceEntry(decision="sub", ref="summarize", shape="Pipeline"),
        TraceEntry(decision="finish"),
    ]
    plan = generalize_trace_to_plan(trace)
    assert plan.op.value == "seq"  # straight-line pipeline


def test_extract_plan_returns_diagnostics_without_raising():
    trace = [TraceEntry(decision="call", ref="search"), TraceEntry(decision="call", ref="writer")]
    caps = CapabilityManifest.from_dict(
        {"tools": [{"name": "search", "effect": "read", "idempotency": "native"}], "budget": {"usd": 100}}
    )
    plan, diags = extract_plan(trace, caps)
    assert any(d.code == "PLAN_TOOL_UNGRANTED" for d in diags)


def test_promote_plan_enforces_admission():
    trace = [TraceEntry(decision="call", ref="writer")]
    caps = CapabilityManifest.from_dict({"tools": [], "budget": {"usd": 100}})
    with pytest.raises(PlanRejected):
        promote_plan(trace, caps)


def test_promote_plan_succeeds_when_granted():
    trace = [TraceEntry(decision="call", ref="search")]
    caps = CapabilityManifest.from_dict(
        {"tools": [{"name": "search", "effect": "read", "idempotency": "native"}], "budget": {"usd": 100}}
    )
    plan = promote_plan(trace, caps)
    assert plan.op.value == "prim"


# --------------------------------------------------------------------------- #
# Deploy pipeline (freeze -> validate -> §9 -> §5).
# --------------------------------------------------------------------------- #
def test_deploy_happy_path_returns_runnable_artifact():
    snap = snapshot_from_listings({"srv": {
        "a": {"inputSchema": {}, "annotations": {"readOnlyHint": True, "idempotentHint": True}},
        "b": {"inputSchema": {}, "annotations": {"readOnlyHint": True, "idempotentHint": True}},
    }})
    d = deploy(seq(call(mcp("srv", "a")), call(mcp("srv", "b"))), snap)
    assert len(d.manifest) == 2
    assert "op" in d.flow_json and isinstance(d.manifest_json, dict)
    assert not d.warnings


def test_deploy_blocks_write_in_race():
    d_snap = mixed_snapshot()
    with pytest.raises(ValidationError):
        deploy(race(call(mcp("srv", "read")), call(mcp("srv", "writer"))), d_snap)


def test_deploy_blocks_ungranted_tool():
    snap = read_snapshot("a", "b")
    caps = CapabilityManifest.from_dict({
        "tools": [{"name": "srv/a", "effect": "read", "idempotency": "native"}],
        "mcp_servers": {"srv": None},
    })
    with pytest.raises(ValidationError):
        deploy(seq(call(mcp("srv", "a")), call(mcp("srv", "b"))), snap, capabilities=caps)


def test_deploy_override_admits_asserted_tool_into_race():
    snap = mixed_snapshot()
    caps = CapabilityManifest.from_dict({"tools": [
        {"name": "srv/read", "effect": "read", "idempotency": "native"},
        {"name": "srv/writer", "effect": "read", "idempotency": "required"},
    ], "mcp_servers": {"srv": None}})
    d = deploy(race(call(mcp("srv", "read")), call(mcp("srv", "writer"))), snap, capabilities=caps)
    assert len(d.manifest) == 2


def test_deploy_non_strict_returns_diagnostics():
    d = deploy(race(call(mcp("srv", "read")), call(mcp("srv", "writer"))), mixed_snapshot(), strict=False)
    assert any(x.severity == "error" for x in d.diagnostics)


def test_deploy_per_run_refresh_seam():
    snap = read_snapshot("a")
    calls = {"n": 0}

    def source():
        calls["n"] += 1
        return snap

    d = deploy(call(mcp("srv", "a")), snap, freeze_timing="per_run", snapshot_source=source)
    assert d.freeze_timing == "per_run"
    d2 = d.refresh()
    assert calls["n"] == 1 and len(d2.manifest) == 1


# --------------------------------------------------------------------------- #
# Replay/freeze artifact hash (§6.2).
# --------------------------------------------------------------------------- #
def test_brain_tools_accepts_list_and_stores_tuple():
    assert Brain(name="list.tools.brain", model="test", tools=["a", "b"]).tools == ("a", "b")


def _pure_artifact_fn(value):
    return value


def _artifact_brain(name: str = "artifact.brain", *, system: str = "original") -> Brain:
    return Brain(
        name=name,
        model="test-model",
        system=system,
        reply_schema={"type": "object"},
        tools=("srv/a",),
    )


def test_deployment_artifact_hash_is_stable_for_same_inputs(monkeypatch):
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.identity",
        PureEntry("artifact.identity", _pure_artifact_fn, "pure:stable"),
    )
    monkeypatch.setitem(dotctx._BRAINS, "artifact.brain", _artifact_brain())
    snap = read_snapshot("a")
    flow = seq(arr("artifact.identity"), think("artifact.brain"), call(mcp("srv", "a")))

    first = deploy(flow, snap)
    second = deploy(flow, snap)

    assert first.artifact_components == second.artifact_components
    assert first.artifact_hash == second.artifact_hash
    assert first.artifact_components["pureSourceHashes"] == {"artifact.identity": "pure:stable"}
    assert first.artifact_components["brains"]["artifact.brain"]["system"] == "original"
    assert first.artifact_components["executionPolicy"] is None


def test_deployment_artifact_hash_changes_with_flow_change(monkeypatch):
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.identity",
        PureEntry("artifact.identity", _pure_artifact_fn, "pure:stable"),
    )
    snap = read_snapshot("a", "b")

    first = deploy(seq(arr("artifact.identity"), call(mcp("srv", "a"))), snap)
    second = deploy(seq(arr("artifact.identity"), call(mcp("srv", "a")), call(mcp("srv", "b"))), snap)

    assert first.artifact_hash != second.artifact_hash


def test_deployment_artifact_hash_changes_with_referenced_pure_source(monkeypatch):
    snap = read_snapshot("a")
    flow = seq(arr("artifact.identity"), call(mcp("srv", "a")))
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.identity",
        PureEntry("artifact.identity", _pure_artifact_fn, "pure:before"),
    )
    first = deploy(flow, snap)
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.identity",
        PureEntry("artifact.identity", _pure_artifact_fn, "pure:after"),
    )
    second = deploy(flow, snap)

    assert first.artifact_hash != second.artifact_hash


def test_deployment_artifact_hash_changes_with_referenced_brain(monkeypatch):
    snap = read_snapshot()
    flow = think("artifact.brain")
    monkeypatch.setitem(dotctx._BRAINS, "artifact.brain", _artifact_brain(system="before"))
    first = deploy(flow, snap)
    monkeypatch.setitem(dotctx._BRAINS, "artifact.brain", _artifact_brain(system="after"))
    second = deploy(flow, snap)

    assert first.artifact_hash != second.artifact_hash


def test_deployment_artifact_hash_changes_with_capabilities():
    snap = read_snapshot("a")
    flow = call(mcp("srv", "a"))
    low_budget = CapabilityManifest.from_dict({"budget": {"usd": 1.0}})
    high_budget = CapabilityManifest.from_dict({"budget": {"usd": 2.0}})

    first = deploy(flow, snap, capabilities=low_budget)
    second = deploy(flow, snap, capabilities=high_budget)

    assert first.artifact_hash != second.artifact_hash


def test_deployment_artifact_hash_changes_with_framework_version(monkeypatch):
    snap = read_snapshot("a")
    flow = call(mcp("srv", "a"))

    first = deploy(flow, snap)

    monkeypatch.setattr(composable_agents, "__version__", "artifact-test-version")
    second = deploy(flow, snap)

    assert first.artifact_hash != second.artifact_hash


def test_deployment_artifact_components_collect_referenced_brains_and_pures(monkeypatch):
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.arr",
        PureEntry("artifact.arr", _pure_artifact_fn, "pure:arr"),
    )
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.alt",
        PureEntry("artifact.alt", _pure_artifact_fn, "pure:alt"),
    )
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.until",
        PureEntry("artifact.until", _pure_artifact_fn, "pure:until"),
    )
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.switch",
        PureEntry("artifact.switch", _pure_artifact_fn, "pure:switch"),
    )
    monkeypatch.setitem(
        purity._REGISTRY,
        "artifact.reducer",
        PureEntry("artifact.reducer", _pure_artifact_fn, "pure:reducer"),
    )
    monkeypatch.setitem(dotctx._BRAINS, "artifact.brain", _artifact_brain())
    monkeypatch.setitem(
        dotctx._BRAINS,
        "artifact.controller",
        _artifact_brain("artifact.controller", system="controller"),
    )
    monkeypatch.setitem(
        dotctx._BRAINS,
        "artifact.planner",
        _artifact_brain("artifact.planner", system="planner"),
    )
    fan = par(arr("artifact.arr"), arr("artifact.arr"))
    fan.merge = Merge(kind="all", reducer="artifact.reducer")
    flow = seq(
        arr("artifact.arr"),
        alt("artifact.alt", think("artifact.brain"), app("artifact.controller")),
        alt(
            select="artifact.switch",
            cases={"x": arr("artifact.arr")},
            default=arr("artifact.arr"),
        ),
        iter_up_to(2, stage("artifact.planner"), until="artifact.until"),
        fan,
    )

    d = deploy(flow, read_snapshot(), strict=False)

    assert d.artifact_components["pureSourceHashes"] == {
        "artifact.alt": "pure:alt",
        "artifact.arr": "pure:arr",
        "artifact.reducer": "pure:reducer",
        "artifact.switch": "pure:switch",
        "artifact.until": "pure:until",
    }
    assert sorted(d.artifact_components["brains"]) == [
        "artifact.brain",
        "artifact.controller",
        "artifact.planner",
    ]
