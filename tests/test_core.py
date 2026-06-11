"""Core compile-path unit tests (no Temporal required)."""

from __future__ import annotations

import pytest

from composable_agents import (
    Shape, Effect, Idempotency, Contract,
    Ann,
    arr,
    call, mcp, seq, par, alt, iter_up_to, stage, app,
    sub, race, hedge, quorum, human_gate, HUMAN_GATE_TOOL,
    freeze, validate, blocking, register_pure,
    CapabilityManifest, ToolContract, manifest_to_json, manifest_from_json,
    estimate_cost, admit_plan, check_race_admission,
)
from composable_agents.contracts import FrozenTool, McpAnnotations, definition_hash, execution_hash
from composable_agents.errors import FreezeError, PlanRejected
from composable_agents.ir import Node, canonical_json
from composable_agents.kinds import Op
from composable_agents.transforms import normalize_ids
from composable_agents.shapes import surface_shape, closed_shape
from conftest import read_snapshot, mixed_snapshot


# --------------------------------------------------------------------------- #
# Shape lattice.
# --------------------------------------------------------------------------- #
def test_surface_shape_climbs_the_lattice():
    assert surface_shape(call("a")) == Shape.PIPELINE
    assert surface_shape(seq(call("a"), call("b"))) == Shape.PIPELINE
    assert surface_shape(par(call("a"), call("b"))) == Shape.DATAFLOW
    assert surface_shape(alt("p", call("a"), call("b"))) == Shape.BRANCHING
    assert surface_shape(iter_up_to(3, call("a"))) == Shape.FEEDBACK
    assert surface_shape(stage("planner")) == Shape.STAGED
    agent = app("ctrl", tools=["a"], subflows=["child"], budget={"cost": 1}, max_rounds=2)
    assert surface_shape(agent) == Shape.AGENT
    agent_json = agent.to_json()
    assert agent_json["tools"] == ["a"]
    assert agent_json["subflows"] == ["child"]
    assert agent_json["budget"] == {"cost": 1}
    assert agent_json["maxRounds"] == 2
    assert "max_rounds" not in agent_json


def test_join_takes_the_max_shape():
    # A pipeline containing a branching is at least Branching.
    f = seq(call("a"), alt("p", call("b"), call("c")))
    assert surface_shape(f) == Shape.BRANCHING


def test_sub_is_opaque_at_surface_but_revealed_when_closed():
    f = sub("child", Contract.staged())
    # Surface treats a Sub as an opaque Pipeline...
    assert surface_shape(f) == Shape.PIPELINE
    # ...while the closed shape reveals the contracted shape.
    assert closed_shape(f) == Shape.STAGED


# --------------------------------------------------------------------------- #
# Contracts + manifest round-trip.
# --------------------------------------------------------------------------- #
def test_canonical_json_rejects_non_json_values():
    class NotJson:
        pass

    with pytest.raises(TypeError):
        canonical_json({"payload": NotJson()})


def test_existing_fixture_json_stays_structurally_serializable():
    flow = seq(call(mcp("srv", "a")), alt("route", call("left"), call("right")))
    before = flow.to_json()

    encoded = canonical_json(before)

    assert encoded
    assert flow.to_json() == before


def test_arr_args_absent_from_json_when_not_present():
    node = arr("static_args.absent")

    encoded = node.to_json()

    assert encoded == {"op": "arr", "id": node.id, "pure": "static_args.absent"}


def test_arr_args_round_trip_when_present():
    node = arr(
        "static_args.present",
        args={"field": "title", "nested": {"limit": 3, "enabled": True}},
    )

    encoded = node.to_json()
    back = Node.from_json(encoded)
    normalized = normalize_ids(back)

    assert encoded["args"] == {"field": "title", "nested": {"limit": 3, "enabled": True}}
    assert back.to_json() == encoded
    assert normalized.to_json()["args"] == encoded["args"]
    assert canonical_json(encoded)


def test_arr_args_change_flow_content_hash():
    first = normalize_ids(Node.from_json(arr("static_args.hash", args={"key": "a"}).to_json()))
    second = normalize_ids(Node.from_json(arr("static_args.hash", args={"key": "b"}).to_json()))

    assert canonical_json(first.to_json()) != canonical_json(second.to_json())


def test_manifest_json_round_trip():
    fr = freeze(seq(call(mcp("srv", "a")), call(mcp("srv", "b"))), read_snapshot("a", "b"))
    j = manifest_to_json(fr.manifest)
    back = manifest_from_json(j)
    assert set(back.keys()) == set(fr.manifest.keys())
    for h, tool in fr.manifest.items():
        assert back[h].ref.to_json() == tool.ref.to_json()
        assert back[h].contract.effect == tool.contract.effect
        assert back[h].definition_hash == tool.definition_hash
        assert back[h].execution_hash == tool.execution_hash
        assert h == tool.execution_hash


def test_tool_hashes_split_definition_from_execution_identity():
    ref = mcp("srv", "lookup")
    contract = ToolContract(Effect.READ, Idempotency.NATIVE)
    output_a = {"type": "object", "properties": {"a": {"type": "string"}}}
    output_b = {"type": "object", "properties": {"b": {"type": "string"}}}

    base = FrozenTool.create(ref, {}, contract, output_schema=output_a, asserted=False)
    same = FrozenTool.create(ref, {}, contract, output_schema=output_a, asserted=False)
    changed_output = FrozenTool.create(ref, {}, contract, output_schema=output_b, asserted=False)
    changed_contract = FrozenTool.create(
        ref,
        {},
        ToolContract(Effect.WRITE, Idempotency.NATIVE),
        output_schema=output_a,
        asserted=False,
    )
    changed_asserted = FrozenTool.create(ref, {}, contract, output_schema=output_a, asserted=True)

    assert base.definition_hash == same.definition_hash
    assert base.execution_hash == same.execution_hash
    assert base.execution_hash == base.hash
    assert base.definition_hash != changed_output.definition_hash
    assert base.execution_hash != changed_output.execution_hash
    assert base.definition_hash == changed_contract.definition_hash
    assert base.execution_hash != changed_contract.execution_hash
    assert base.definition_hash == changed_asserted.definition_hash
    assert base.execution_hash != changed_asserted.execution_hash


def test_empty_annotations_hash_like_absent_annotations():
    ref = mcp("srv", "lookup")
    contract = ToolContract(Effect.READ, Idempotency.NATIVE)
    absent = FrozenTool.create(ref, {}, contract, annotations=None)
    empty = FrozenTool.create(ref, {}, contract, annotations=McpAnnotations())

    assert absent.definition_hash == empty.definition_hash
    assert absent.execution_hash == empty.execution_hash


def test_hash_helpers_include_expected_identity_parts():
    ref = mcp("srv", "lookup")
    contract = ToolContract(Effect.READ, Idempotency.NATIVE)
    base_definition = definition_hash(ref, {}, {"type": "object"}, "1")
    same_definition = definition_hash(ref, {}, {"type": "object"}, "1")
    changed_definition = definition_hash(ref, {}, {"type": "array"}, "1")

    assert base_definition == same_definition
    assert base_definition != changed_definition
    assert execution_hash(base_definition, contract, asserted=False) != execution_hash(
        base_definition, contract, asserted=True
    )


# --------------------------------------------------------------------------- #
# Freeze: hashing, determinism, reserved gate, cycle rejection.
# --------------------------------------------------------------------------- #
def test_freeze_is_deterministic_and_binds_hashes():
    flow = seq(call(mcp("srv", "a")), call(mcp("srv", "b")))
    f1 = freeze(flow, read_snapshot("a", "b"))
    f2 = freeze(flow, read_snapshot("a", "b"))
    assert f1.flow.to_json() == f2.flow.to_json()  # normalized + stable
    # every call node carries a frozen hash present in the manifest
    for node in f1.flow.walk():
        if node.step and getattr(node.step, "frozen_hash", None):
            assert node.step.frozen_hash in f1.manifest


def test_freeze_version_changes_hash():
    a = freeze(call(mcp("srv", "a")), read_snapshot("a", version="1"))
    b = freeze(call(mcp("srv", "a")), read_snapshot("a", version="2"))
    (ha,) = list(a.manifest.keys())
    (hb,) = list(b.manifest.keys())
    assert ha != hb  # version is bound into the content hash


def test_human_gate_freezes_to_reserved_external_tool():
    gate = human_gate(prompt="approve?", timeout_s=60)
    assert gate.prompt == "approve?"
    assert gate.to_json()["ann"] == {"timeout": 60}
    assert "prompt" not in gate.to_json()
    fr = freeze(gate, read_snapshot())
    (tool,) = list(fr.manifest.values())
    assert tool.ref.to_json()["name"] == HUMAN_GATE_TOOL
    assert tool.contract.effect == Effect.EXTERNAL


def test_freeze_rejects_unresolved_tool():
    with pytest.raises(FreezeError):
        freeze(call(mcp("srv", "missing")), read_snapshot("a"))


# --------------------------------------------------------------------------- #
# Validate.
# --------------------------------------------------------------------------- #
def test_validate_clean_flow_has_no_blocking():
    fr = freeze(seq(call(mcp("srv", "a")), call(mcp("srv", "b"))), read_snapshot("a", "b"))
    assert not blocking(validate(fr.flow, fr.manifest))


def test_validate_accepts_arr_static_args_json_object():
    register_pure("static_args.validate.ok", lambda value, **kwargs: (value, kwargs))
    flow = arr(
        "static_args.validate.ok",
        args={"field": "title", "nested": {"limit": 3, "enabled": True, "items": [1, None]}},
    )

    assert not blocking(validate(flow))


def test_validate_rejects_arr_static_args_bad_keys_and_non_json_values():
    register_pure("static_args.validate.bad", lambda value, **kwargs: (value, kwargs))
    bad_key = Node(
        op=Op.ARR,
        id="bad-key",
        pure="static_args.validate.bad",
        args={"not-valid": 1},
    )
    bad_value = Node(
        op=Op.ARR,
        id="bad-value",
        pure="static_args.validate.bad",
        args={"value": object()},
    )

    bad_key_codes = {diag.code for diag in blocking(validate(bad_key))}
    bad_value_codes = {diag.code for diag in blocking(validate(bad_value))}

    assert "ARR_ARGS_BAD_KEY" in bad_key_codes
    assert "ARR_ARGS_NOT_JSON" in bad_value_codes


def test_validate_rejects_arr_static_args_on_non_arr_nodes():
    flow = Node(op=Op.IDENT, id="ident-with-args", args={"field": "title"})

    codes = {diag.code for diag in blocking(validate(flow))}

    assert "ARR_ARGS_ON_NONARR" in codes


def test_validate_blocks_secret_shaped_arr_static_args_at_any_depth():
    register_pure("static_args.validate.secret", lambda value, **kwargs: (value, kwargs))
    flow = arr(
        "static_args.validate.secret",
        args={"layout": [{"safe": 1}, {"Private_Key": "inline-secret"}]},
    )

    diags = blocking(validate(flow))

    assert any(diag.code == "ARR_ARGS_SECRET" for diag in diags)


def test_parallel_validates_without_blocking():
    # A plain parallel is well-formed; the whole-session degrade warning only
    # fires for a WHOLE_SESSION context branch, which this flow does not have.
    fr = freeze(par(call(mcp("srv", "a")), call(mcp("srv", "b"))), read_snapshot("a", "b"))
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
    q = quorum(call("a"), call("b"), call("c"), k=2)
    assert any(n.merge and n.merge.kind == "quorum" and n.merge.quorum_m == 2 for n in q.walk())
    h = hedge(call("a"), call("b"), hedge_ms=50)
    assert any(n.merge and n.merge.kind == "hedge" and n.merge.hedge_ms == 50 for n in h.walk())


# --------------------------------------------------------------------------- #
# §5 race admission.
# --------------------------------------------------------------------------- #
def test_race_admission_blocks_write_branch():
    fr = freeze(race(call(mcp("srv", "read")), call(mcp("srv", "writer"))), mixed_snapshot())
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
    fr = freeze(race(call(mcp("srv", "a")), call(mcp("srv", "b"))), read_snapshot("a", "b"), ov)
    assert not blocking(check_race_admission(fr.flow, fr.manifest))


# --------------------------------------------------------------------------- #
# §8 staged estimation + plan admission.
# --------------------------------------------------------------------------- #
def test_estimate_cost_folds_structure():
    # seq sums; alt takes max; iter multiplies by bound.
    assert Ann(cost=0.5, timeout_s=2).to_json() == {"cost": 0.5, "timeout": 2}
    seq_flow = seq(call("a"), call("b"))
    assert estimate_cost(seq_flow) == estimate_cost(call("a")) + estimate_cost(call("b"))
    alt_flow = alt("p", call("a"), seq(call("b"), call("c")))
    assert estimate_cost(alt_flow) == max(estimate_cost(call("a")),
                                          estimate_cost(seq(call("b"), call("c"))))


def test_admit_plan_rejects_staged_plan_shape():
    parent = CapabilityManifest.from_dict({"tools": [], "budget": {"cost": 1000}})
    # A plan may not itself stage (closed shape > Feedback).
    with pytest.raises(PlanRejected):
        admit_plan(stage("inner"), parent)


def test_admit_plan_rejects_ungranted_tool():
    parent = CapabilityManifest.from_dict(
        {"tools": [{"name": "a", "effect": "read", "idempotency": "native"}], "budget": {"cost": 1000}}
    )
    with pytest.raises(PlanRejected):
        admit_plan(seq(call("a"), call("b")), parent)


# --------------------------------------------------------------------------- #
# §9 capabilities.
# --------------------------------------------------------------------------- #
def test_capability_overrides_assert_contract():
    caps = CapabilityManifest.from_dict({"tools": [
        {
            "name": "srv/writer",
            "effect": "read",
            "idempotency": "required",
            "approval": True,
            "maxCalls": 1,
        },
    ], "brains": ["summarizer"], "subflows": ["child"]})
    ov = caps.overrides()
    c = ov.get("srv/writer")
    assert c is not None and c.effect == Effect.READ and c.idempotency == Idempotency.REQUIRED
    assert caps.tools["srv/writer"].approval is True
    assert caps.tools["srv/writer"].max_calls == 1
    assert caps.brains == {"summarizer"} and caps._has_brains
    assert caps.subflows == {"child"} and caps._has_subflows


def test_capability_enforce_blocks_ungranted_model_or_tool():
    caps = CapabilityManifest.from_dict({
        "tools": [{"name": "srv/a", "effect": "read", "idempotency": "native"}],
        "mcp_servers": {"srv": None},
    })
    fr = freeze(seq(call(mcp("srv", "a")), call(mcp("srv", "b"))), read_snapshot("a", "b"))
    diags = caps.enforce_compile(fr.flow)
    assert blocking(diags)
