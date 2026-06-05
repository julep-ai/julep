from __future__ import annotations

import pytest

pytest.importorskip("temporalio")

from composable_agents import (
    Brain,
    CapabilityManifest,
    Effect,
    FrozenTool,
    Idempotency,
    ToolContract,
    call,
    mcp,
    register_brain,
)
from composable_agents.agent_loop import TraceEntry
from composable_agents.contracts import CONSERVATIVE_DEFAULT, manifest_to_json
from composable_agents.errors import PlanRejected
from composable_agents.execution.activities import (
    CompilePlanInput,
    WorkerContext,
    compilePlan,
    configure,
)
from composable_agents.execution.interpreter import call_contract
from composable_agents.ir import CallStep, Node
from composable_agents.staged import bind_plan_to_manifest, validate_plan, admit_plan
from conftest import run


def _caps(*names: str) -> CapabilityManifest:
    return CapabilityManifest.from_dict(
        {
            "tools": [
                {"name": name, "effect": "read", "idempotency": "required"}
                for name in names
            ],
            "budget": {"cost": 100},
        }
    )


def _tool_ungranted_codes(diags) -> list[str]:  # noqa: ANN001
    return [d.code for d in diags if d.code == "PLAN_TOOL_UNGRANTED"]


def _frozen(
    name: str,
    *,
    effect: Effect = Effect.READ,
    idempotency: Idempotency = Idempotency.REQUIRED,
    asserted: bool = True,
) -> FrozenTool:
    return FrozenTool.create(
        mcp("srv", name),
        {"type": "object"},
        ToolContract(effect, idempotency),
        output_schema={"type": "object"},
        asserted=asserted,
    )


def _call_step(plan: Node) -> CallStep:
    assert isinstance(plan.step, CallStep)
    return plan.step


def test_bind_plan_sets_frozen_hash_and_real_contract() -> None:
    tool = _frozen("lookup", effect=Effect.READ, idempotency=Idempotency.REQUIRED)
    manifest = {tool.execution_hash: tool}
    plan = call(mcp("srv", "lookup"))

    bound = bind_plan_to_manifest(plan, manifest)

    assert bound is not plan
    assert _call_step(plan).frozen_hash is None
    assert _call_step(bound).frozen_hash == tool.execution_hash
    assert call_contract(bound, manifest) == tool.contract
    assert call_contract(bound, manifest) != CONSERVATIVE_DEFAULT


def test_unknown_tool_is_rejected_as_unbound() -> None:
    tool = _frozen("lookup")
    manifest = {tool.execution_hash: tool}
    plan = call(mcp("srv", "invented"))

    diags = validate_plan(plan, _caps("srv/invented"), manifest)

    assert any(d.code == "PLAN_TOOL_UNBOUND" for d in diags)


def test_ambiguous_logical_ref_rejected_unless_hash_pinned() -> None:
    read_tool = _frozen("lookup", effect=Effect.READ, idempotency=Idempotency.REQUIRED)
    write_tool = _frozen("lookup", effect=Effect.WRITE, idempotency=Idempotency.NONE)
    manifest = {
        read_tool.execution_hash: read_tool,
        write_tool.execution_hash: write_tool,
    }

    unpinned = call(mcp("srv", "lookup"))
    diags = validate_plan(unpinned, _caps("srv/lookup"), manifest)
    assert any(d.code == "PLAN_TOOL_AMBIGUOUS" for d in diags)

    pinned = call(mcp("srv", "lookup"))
    _call_step(pinned).frozen_hash = write_tool.execution_hash
    bound = bind_plan_to_manifest(pinned, manifest)
    assert _call_step(bound).frozen_hash == write_tool.execution_hash
    assert call_contract(bound, manifest) == write_tool.contract


def test_admit_plan_rejects_invented_and_returns_bound_plan() -> None:
    tool = _frozen("lookup")
    manifest = {tool.execution_hash: tool}

    with pytest.raises(PlanRejected) as rejected:
        admit_plan(call(mcp("srv", "invented")), _caps("srv/invented"), manifest)
    assert "PLAN_TOOL_UNBOUND" in str(rejected.value)

    bound = admit_plan(call(mcp("srv", "lookup")), _caps("srv/lookup"), manifest)
    assert _call_step(bound).frozen_hash == tool.execution_hash


def test_compile_plan_returns_bound_plan_json() -> None:
    planner = "staged-binding-planner"
    tool = _frozen("lookup")
    manifest = {tool.execution_hash: tool}
    expected_plan = call(mcp("srv", "lookup")).to_json()

    async def llm(_brain: Brain, _value: object) -> dict[str, object]:
        return {"plan": expected_plan}

    register_brain(Brain(name=planner, model="test", system=""))
    configure(WorkerContext(llm=llm, capabilities=_caps("srv/lookup")))
    try:
        raw = run(
            compilePlan(
                CompilePlanInput(
                    planner=planner,
                    value={"input": 1},
                    cid="compile-1",
                    manifest=manifest_to_json(manifest),
                )
            )
        )
    finally:
        configure(WorkerContext())

    compiled = Node.from_json(raw)
    assert _call_step(compiled).frozen_hash == tool.execution_hash


def test_trace_entry_refs_round_trip() -> None:
    entry = TraceEntry(
        decision="call",
        ref="search",
        cost=1.25,
        input_ref="sha256:input",
        output_ref="sha256:output",
        schema_ref="sha256:schema",
    )

    assert TraceEntry.from_json(entry.to_json()) == entry


def test_validate_plan_absent_tools_section_allows_manifest_bound_call() -> None:
    tool = _frozen("lookup")
    manifest = {tool.execution_hash: tool}
    parent = CapabilityManifest.from_dict({"budget": {"cost": 100}})

    diags = validate_plan(call(mcp("srv", "lookup")), parent, manifest)

    assert _tool_ungranted_codes(diags) == []


def test_validate_plan_present_empty_tools_denies_every_call() -> None:
    tool = _frozen("lookup")
    manifest = {tool.execution_hash: tool}
    parent = CapabilityManifest.from_dict({"tools": [], "budget": {"cost": 100}})

    diags = validate_plan(call(mcp("srv", "lookup")), parent, manifest)

    assert _tool_ungranted_codes(diags) == ["PLAN_TOOL_UNGRANTED"]


def test_validate_plan_present_tools_denies_only_ungranted_calls() -> None:
    lookup = _frozen("lookup")
    other = _frozen("other")
    manifest = {lookup.execution_hash: lookup, other.execution_hash: other}
    parent = _caps("srv/lookup")

    allowed = validate_plan(call(mcp("srv", "lookup")), parent, manifest)
    denied = validate_plan(call(mcp("srv", "other")), parent, manifest)

    assert _tool_ungranted_codes(allowed) == []
    assert _tool_ungranted_codes(denied) == ["PLAN_TOOL_UNGRANTED"]
