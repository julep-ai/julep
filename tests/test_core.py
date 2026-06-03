"""Core compile-path unit tests (no Temporal required)."""

from __future__ import annotations

import pytest

from composable_agents import (
    Shape, Effect, Idempotency, SummaryPolicy, Contract,
    call, mcp_call, think, pipeline, parallel, route, critique, stage, escalate,
    subagent, race, hedge, quorum, map_reduce, human_gate, HUMAN_GATE_TOOL,
    freeze, validate, blocking, deploy, snapshot_from_listings,
    CapabilityManifest, ToolContract, manifest_to_json, manifest_from_json,
    estimate_cost, validate_plan, admit_plan, check_race_admission,
    register_pure,
)
from composable_agents.errors import FreezeError, ValidationError, PlanRejected
from composable_agents.shapes import surface_shape, closed_shape
from conftest import read_snapshot, mixed_snapshot


# --------------------------------------------------------------------------- #
# Shape lattice.
# --------------------------------------------------------------------------- #
def test_surface_shape_climbs_the_lattice():
    assert surface_shape(call("a")) == Shape.PIPELINE
    assert surface_shape(pipeline(call("a"), call("b"))) == Shape.PIPELINE
    assert surface_shape(parallel(call("a"), call("b"))) == Shape.DATAFLOW
    assert surface_shape(route("p", call("a"), call("b"))) == Shape.BRANCHING
    assert surface_shape(critique(3, call("a"))) == Shape.FEEDBACK
    assert surface_shape(stage("planner")) == Shape.STAGED
    assert surface_shape(escalate("ctrl")) == Shape.AGENT


def test_join_takes_the_max_shape():
    # A pipeline containing a branching is at least Branching.
    f = pipeline(call("a"), route("p", call("b"), call("c")))
    assert surface_shape(f) == Shape.BRANCHING


def test_sub_is_opaque_at_surface_but_revealed_when_closed():
    f = subagent("child", Contract.staged())
    # Surface treats a Sub as an opaque Pipeline...
    assert surface_shape(f) == Shape.PIPELINE
    # ...while the closed shape reveals the contracted shape.
    assert closed_shape(f) == Shape.STAGED


# --------------------------------------------------------------------------- #
# Contracts + manifest round-trip.
# --------------------------------------------------------------------------- #
def test_manifest_json_round_trip():
    fr = freeze(pipeline(mcp_call("srv", "a"), mcp_call("srv", "b")), read_snapshot("a", "b"))
    j = manifest_to_json(fr.manifest)
    back = manifest_from_json(j)
    assert set(back.keys()) == set(fr.manifest.keys())
    for h, tool in fr.manifest.items():
        assert back[h].ref.to_json() == tool.ref.to_json()
        assert back[h].contract.effect == tool.contract.effect


# --------------------------------------------------------------------------- #
# Freeze: hashing, determinism, reserved gate, cycle rejection.
# --------------------------------------------------------------------------- #
def test_freeze_is_deterministic_and_binds_hashes():
    flow = pipeline(mcp_call("srv", "a"), mcp_call("srv", "b"))
    f1 = freeze(flow, read_snapshot("a", "b"))
    f2 = freeze(flow, read_snapshot("a", "b"))
    assert f1.flow.to_json() == f2.flow.to_json()  # normalized + stable
    # every call node carries a frozen hash present in the manifest
    for node in f1.flow.walk():
        if node.step and getattr(node.step, "frozen_hash", None):
            assert node.step.frozen_hash in f1.manifest


def test_freeze_version_changes_hash():
    a = freeze(mcp_call("srv", "a"), read_snapshot("a", version="1"))
    b = freeze(mcp_call("srv", "a"), read_snapshot("a", version="2"))
    (ha,) = list(a.manifest.keys())
    (hb,) = list(b.manifest.keys())
    assert ha != hb  # version is bound into the content hash


def test_human_gate_freezes_to_reserved_external_tool():
    fr = freeze(human_gate(), read_snapshot())
    (tool,) = list(fr.manifest.values())
    assert tool.ref.to_json()["name"] == HUMAN_GATE_TOOL
    assert tool.contract.effect == Effect.EXTERNAL


def test_freeze_rejects_unresolved_tool():
    with pytest.raises(FreezeError):
        freeze(mcp_call("srv", "missing"), read_snapshot("a"))


# --------------------------------------------------------------------------- #
# Validate.
# --------------------------------------------------------------------------- #
def test_validate_clean_flow_has_no_blocking():
    fr = freeze(pipeline(mcp_call("srv", "a"), mcp_call("srv", "b")), read_snapshot("a", "b"))
    assert not blocking(validate(fr.flow, fr.manifest))


def test_parallel_validates_without_blocking():
    # A plain parallel is well-formed; the whole-session degrade warning only
    # fires for a WHOLE_SESSION context branch, which this flow does not have.
    fr = freeze(parallel(mcp_call("srv", "a"), mcp_call("srv", "b")), read_snapshot("a", "b"))
    assert not blocking(validate(fr.flow, fr.manifest))


# --------------------------------------------------------------------------- #
# Derived combinators lower to a uniform race spine.
# --------------------------------------------------------------------------- #
def test_race_lowers_to_par_with_merge_on_every_node():
    f = race(call("a"), call("b"), call("c"))
    merges = [n.merge for n in f.walk() if n.merge is not None]
    assert merges, "race must annotate merge"
    assert all(m.kind == "race" for m in merges)


def test_quorum_sets_m_and_hedge_sets_timing():
    q = quorum(call("a"), call("b"), call("c"), m=2)
    assert any(n.merge and n.merge.kind == "quorum" and n.merge.quorum_m == 2 for n in q.walk())
    h = hedge(call("a"), call("b"), after_ms=50)
    assert any(n.merge and n.merge.kind == "hedge" and n.merge.hedge_ms == 50 for n in h.walk())


# --------------------------------------------------------------------------- #
# §5 race admission.
# --------------------------------------------------------------------------- #
def test_race_admission_blocks_write_branch():
    fr = freeze(race(mcp_call("srv", "read"), mcp_call("srv", "writer")), mixed_snapshot())
    diags = check_race_admission(fr.flow, fr.manifest)
    assert blocking(diags)


def test_race_admission_allows_asserted_idempotent_branches():
    # MCP hints are untrusted, so a race needs *asserted* contracts; assert both
    # branches read/required via capability overrides at freeze.
    from composable_agents import CapabilityOverrides

    ov = CapabilityOverrides(contracts={
        "srv/a": ToolContract(Effect.READ, Idempotency.REQUIRED),
        "srv/b": ToolContract(Effect.READ, Idempotency.REQUIRED),
    })
    fr = freeze(race(mcp_call("srv", "a"), mcp_call("srv", "b")), read_snapshot("a", "b"), ov)
    assert not blocking(check_race_admission(fr.flow, fr.manifest))


# --------------------------------------------------------------------------- #
# §8 staged estimation + plan admission.
# --------------------------------------------------------------------------- #
def test_estimate_cost_folds_structure():
    # seq sums; alt takes max; iter multiplies by bound.
    seq = pipeline(call("a"), call("b"))
    assert estimate_cost(seq) == estimate_cost(call("a")) + estimate_cost(call("b"))
    alt = route("p", call("a"), pipeline(call("b"), call("c")))
    assert estimate_cost(alt) == max(estimate_cost(call("a")),
                                     estimate_cost(pipeline(call("b"), call("c"))))


def test_admit_plan_rejects_staged_plan_shape():
    parent = CapabilityManifest.from_dict({"tools": [], "budget": {"usd": 1000}})
    # A plan may not itself stage (closed shape > Feedback).
    with pytest.raises(PlanRejected):
        admit_plan(stage("inner"), parent)


def test_admit_plan_rejects_ungranted_tool():
    parent = CapabilityManifest.from_dict(
        {"tools": [{"name": "a", "effect": "read", "idempotency": "native"}], "budget": {"usd": 1000}}
    )
    with pytest.raises(PlanRejected):
        admit_plan(pipeline(call("a"), call("b")), parent)


# --------------------------------------------------------------------------- #
# §9 capabilities.
# --------------------------------------------------------------------------- #
def test_capability_overrides_assert_contract():
    caps = CapabilityManifest.from_dict({"tools": [
        {"name": "srv/writer", "effect": "read", "idempotency": "required"},
    ]})
    ov = caps.overrides()
    c = ov.get("srv/writer")
    assert c is not None and c.effect == Effect.READ and c.idempotency == Idempotency.REQUIRED


def test_capability_enforce_blocks_ungranted_model_or_tool():
    caps = CapabilityManifest.from_dict({
        "tools": [{"name": "srv/a", "effect": "read", "idempotency": "native"}],
        "mcp_servers": {"srv": None},
    })
    fr = freeze(pipeline(mcp_call("srv", "a"), mcp_call("srv", "b")), read_snapshot("a", "b"))
    diags = caps.enforce_compile(fr.flow)
    assert blocking(diags)
