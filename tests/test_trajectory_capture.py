"""Lane B (Capture): the effect layer feeds the trajectory plane.

Trajectory capture lives only in the shared, backend-neutral effect functions
(:func:`composable_agents.execution.effects.callHand` / ``invokeBrain`` /
``runSub``), so BOTH the Temporal and DBOS backends — which both call these
effect bodies — get capture for free.

The contract these tests pin:

* each effect captures one ``did`` step (input + output) with value refs that
  resolve through the blob store, keyed by ``tenant == root_run_id``;
* capture is best-effort: a sink that raises must leave the effect RESULT
  byte-identical (CRITICAL);
* a blob put that fails marks that ref unavailable (``None``) yet still records
  the step, and the effect result is unchanged.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import pytest

from composable_agents.dotctx import Brain, register_brain
from composable_agents.execution.blobstore import InMemoryBlobStore, parse_ref
from composable_agents.execution.effects import (
    CallHandInput,
    InvokeBrainInput,
    RunSubInput,
    WorkerContext,
    callHand,
    configure,
    invokeBrain,
    record_marker_step,
    runSub,
    set_trajectory_sink,
)
from composable_agents.trajectory import (
    InMemoryTrajectoryStore,
    TrajectoryStep,
    TrajectoryValue,
    trajectory_best_effort_failures,
)

ROOT = "run-root"
RUN = "run-root"

CALL_INPUT = {"q": "needle"}
CALL_OUTPUT = {"hits": 3}
BRAIN_INPUT = {"prompt": "summarize"}
BRAIN_OUTPUT = {"reply": "done"}
SUB_INPUT = {"items": [1, 2, 3]}
SUB_OUTPUT = {"scored": [0.1, 0.2, 0.3]}


# --------------------------------------------------------------------------- #
# Fixtures / helpers.
# --------------------------------------------------------------------------- #
def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True).encode()


def _install(
    *,
    sink: Optional[InMemoryTrajectoryStore],
    blob_store: Optional[InMemoryBlobStore],
    mcp_call=None,
    llm=None,
) -> None:
    """Install a worker context and (separately) the module-global trajectory sink."""
    configure(
        WorkerContext(
            mcp_call=mcp_call,
            llm=llm,
            blob_store=blob_store,
            trajectory_sink=sink,
            trajectory_blob_store=blob_store,
        )
    )
    # configure() already installs the sink; set it explicitly too so the test is
    # robust to context wiring and so teardown can disable capture cleanly.
    set_trajectory_sink(sink, blob_store)


@pytest.fixture(autouse=True)
def _isolate_capture():
    """Each test starts and ends with capture disabled (no leaked module globals)."""
    register_brain(Brain(name="lbcap.summarizer", model="test", system="s"))
    set_trajectory_sink(None, None)
    yield
    set_trajectory_sink(None, None)


def _hand_input(**identity: Any) -> CallHandInput:
    return CallHandInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value=CALL_INPUT,
        cid="call-cid-1",
        run_id=RUN,
        root_run_id=ROOT,
        segment_seq=0,
        node_id="search-node",
        op="call",
        kind="hand",
        causes=("up-1",),
        **identity,
    )


def _brain_input(**identity: Any) -> InvokeBrainInput:
    return InvokeBrainInput(
        brain="lbcap.summarizer",
        value=BRAIN_INPUT,
        cid="brain-cid-1",
        run_id=RUN,
        root_run_id=ROOT,
        segment_seq=0,
        node_id="think-node",
        op="think",
        kind="brain",
        causes=("up-2",),
        **identity,
    )


def _sub_input(**identity: Any) -> RunSubInput:
    return RunSubInput(
        ref="grade-scores",
        value=SUB_INPUT,
        cid="sub-cid-1",
        run_id=RUN,
        root_run_id=ROOT,
        segment_seq=0,
        node_id="sub-node",
        op="sub",
        kind="flow",
        causes=("up-3",),
        **identity,
    )


async def _mcp_caller(server: str, tool: str, value: Any, key: str, principal: Any) -> Any:
    return CALL_OUTPUT


async def _llm_caller(brain: Any, value: Any, principal: Any, transcript: Any) -> Any:
    return BRAIN_OUTPUT


# --------------------------------------------------------------------------- #
# Happy path: each effect captures input + output with value refs.
# --------------------------------------------------------------------------- #
def test_call_hand_captures_input_and_output_step():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _install(sink=sink, blob_store=blobs, mcp_call=_mcp_caller)

    result = asyncio.run(callHand(_hand_input()))
    assert result == CALL_OUTPUT

    steps = sink.list_trajectory_steps(ROOT)
    assert len(steps) == 1
    step = steps[0]
    assert step.op == "call"
    assert step.kind == "hand"
    assert step.status == "did"
    assert step.run_id == RUN
    assert step.root_run_id == ROOT
    assert step.node_id == "search-node"
    assert step.cid == "call-cid-1"
    assert step.causes == ("up-1",)
    assert step.input_ref is not None
    assert step.output_ref is not None

    # Refs are canonical-JSON content addresses, tenant == root_run_id.
    in_tenant, _ = parse_ref(step.input_ref)
    out_tenant, _ = parse_ref(step.output_ref)
    assert in_tenant == ROOT
    assert out_tenant == ROOT
    assert asyncio.run(blobs.get(ROOT, step.input_ref)) == _canonical(CALL_INPUT)
    assert asyncio.run(blobs.get(ROOT, step.output_ref)) == _canonical(CALL_OUTPUT)

    # record_values mirrors the two refs with input/output kinds.
    values = sink.list_trajectory_values(ROOT)
    refs = {v.kind: v.ref for v in values}
    assert refs == {"input": step.input_ref, "output": step.output_ref}
    assert all(v.root_run_id == ROOT and v.step_id == step.step_id for v in values)


def test_invoke_brain_captures_input_and_output_step():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _install(sink=sink, blob_store=blobs, llm=_llm_caller)

    result = asyncio.run(invokeBrain(_brain_input()))
    assert result == BRAIN_OUTPUT

    steps = sink.list_trajectory_steps(ROOT)
    assert len(steps) == 1
    step = steps[0]
    assert step.op == "think"
    assert step.kind == "brain"
    assert step.node_id == "think-node"
    assert step.causes == ("up-2",)
    assert step.input_ref is not None and step.output_ref is not None
    assert asyncio.run(blobs.get(ROOT, step.input_ref)) == _canonical(BRAIN_INPUT)
    assert asyncio.run(blobs.get(ROOT, step.output_ref)) == _canonical(BRAIN_OUTPUT)

    values = {v.kind: v.ref for v in sink.list_trajectory_values(ROOT)}
    assert values == {"input": step.input_ref, "output": step.output_ref}


def test_run_sub_captures_input_and_output_step():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _install(sink=sink, blob_store=blobs)

    result = asyncio.run(runSub(_sub_input(), SUB_OUTPUT))
    assert result == SUB_OUTPUT

    steps = sink.list_trajectory_steps(ROOT)
    assert len(steps) == 1
    step = steps[0]
    assert step.op == "sub"
    assert step.kind == "flow"
    assert step.node_id == "sub-node"
    assert step.causes == ("up-3",)
    assert step.input_ref is not None and step.output_ref is not None
    assert asyncio.run(blobs.get(ROOT, step.input_ref)) == _canonical(SUB_INPUT)
    assert asyncio.run(blobs.get(ROOT, step.output_ref)) == _canonical(SUB_OUTPUT)

    values = {v.kind: v.ref for v in sink.list_trajectory_values(ROOT)}
    assert values == {"input": step.input_ref, "output": step.output_ref}


def test_record_marker_step_root_and_final():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _install(sink=sink, blob_store=blobs)

    asyncio.run(
        record_marker_step(
            kind="root",
            run_id=RUN,
            root_run_id=ROOT,
            segment_seq=0,
            value=SUB_INPUT,
            cid=f"{ROOT}:root",
            value_kind="input",
        )
    )
    asyncio.run(
        record_marker_step(
            kind="final",
            run_id=RUN,
            root_run_id=ROOT,
            segment_seq=0,
            value=SUB_OUTPUT,
            cid=f"{ROOT}:final",
            value_kind="output",
        )
    )

    steps = sink.list_trajectory_steps(ROOT)
    assert [(s.op, s.kind) for s in steps] == [("root", "root"), ("final", "final")]
    root_step, final_step = steps
    assert root_step.input_ref is not None and root_step.output_ref is None
    assert final_step.output_ref is not None and final_step.input_ref is None

    root_tenant, _ = parse_ref(root_step.input_ref)
    final_tenant, _ = parse_ref(final_step.output_ref)
    assert root_tenant == final_tenant == ROOT
    assert asyncio.run(blobs.get(ROOT, root_step.input_ref)) == _canonical(SUB_INPUT)
    assert asyncio.run(blobs.get(ROOT, final_step.output_ref)) == _canonical(SUB_OUTPUT)

    values = {
        v.kind: v.ref
        for v in sink.list_trajectory_values(ROOT)
        if v.step_id in {root_step.step_id, final_step.step_id}
    }
    assert values == {"input": root_step.input_ref, "output": final_step.output_ref}


# --------------------------------------------------------------------------- #
# No run-identity / no sink: capture is a strict no-op (boundary-gated).
# --------------------------------------------------------------------------- #
def test_capture_noop_without_sink():
    blobs = InMemoryBlobStore()
    # No sink installed (autouse fixture set it None); just a worker context.
    configure(WorkerContext(mcp_call=_mcp_caller, blob_store=blobs))
    set_trajectory_sink(None, None)

    result = asyncio.run(callHand(_hand_input()))
    assert result == CALL_OUTPUT  # effect still works, nothing captured


def test_capture_noop_without_root_run_id():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _install(sink=sink, blob_store=blobs, mcp_call=_mcp_caller)

    # An effect input carrying no run identity (the legacy/harness path that only
    # stamps `principal`) must not capture anything.
    inp = CallHandInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value=CALL_INPUT,
        cid="call-cid-2",
    )
    result = asyncio.run(callHand(inp))
    assert result == CALL_OUTPUT
    assert sink.list_trajectory_steps(ROOT) == []


# --------------------------------------------------------------------------- #
# Best-effort: a failing sink leaves the effect RESULT byte-identical (CRITICAL).
# --------------------------------------------------------------------------- #
class _RaisingSink(InMemoryTrajectoryStore):
    def append_steps(self, steps: list[TrajectoryStep]) -> None:
        raise RuntimeError("sink down: append_steps")

    def record_values(self, values: list[TrajectoryValue]) -> None:
        raise RuntimeError("sink down: record_values")


def test_sink_append_steps_raising_keeps_result_byte_identical():
    blobs = InMemoryBlobStore()

    # Baseline result with a healthy sink.
    good = InMemoryTrajectoryStore()
    _install(sink=good, blob_store=blobs, mcp_call=_mcp_caller)
    baseline = asyncio.run(callHand(_hand_input()))

    before = trajectory_best_effort_failures()
    bad = _RaisingSink()
    _install(sink=bad, blob_store=blobs, mcp_call=_mcp_caller)
    result = asyncio.run(callHand(_hand_input()))

    # CRITICAL: the run never sees the sink failure; result is byte-identical.
    assert result == baseline == CALL_OUTPUT
    assert json.dumps(result, sort_keys=True) == json.dumps(baseline, sort_keys=True)
    # The failure was swallowed + counted (append_steps and record_values both raised).
    assert trajectory_best_effort_failures() > before


def test_sink_failure_swallowed_for_all_effects():
    blobs = InMemoryBlobStore()
    bad = _RaisingSink()
    _install(sink=bad, blob_store=blobs, mcp_call=_mcp_caller, llm=_llm_caller)

    assert asyncio.run(callHand(_hand_input())) == CALL_OUTPUT
    assert asyncio.run(invokeBrain(_brain_input())) == BRAIN_OUTPUT
    assert asyncio.run(runSub(_sub_input(), SUB_OUTPUT)) == SUB_OUTPUT


# --------------------------------------------------------------------------- #
# Best-effort: a failing blob store marks refs unavailable; result unchanged.
# --------------------------------------------------------------------------- #
class _FailingBlobStore(InMemoryBlobStore):
    async def put(self, tenant: str, data: bytes) -> str:
        raise RuntimeError("blob store down: put")


def test_blob_put_failure_records_step_with_unavailable_refs():
    sink = InMemoryTrajectoryStore()
    failing = _FailingBlobStore()
    _install(sink=sink, blob_store=failing, mcp_call=_mcp_caller)

    before = trajectory_best_effort_failures()
    result = asyncio.run(callHand(_hand_input()))

    # Effect result is unchanged.
    assert result == CALL_OUTPUT

    # The step is still recorded, with both refs marked unavailable (None).
    steps = sink.list_trajectory_steps(ROOT)
    assert len(steps) == 1
    step = steps[0]
    assert step.op == "call"
    assert step.status == "did"
    assert step.input_ref is None
    assert step.output_ref is None

    # No value rows when there are no refs.
    assert sink.list_trajectory_values(ROOT) == []
    # Two failed blob puts (input + output) were swallowed + counted.
    assert trajectory_best_effort_failures() >= before + 2


def test_blob_put_failure_for_brain_and_sub():
    sink = InMemoryTrajectoryStore()
    failing = _FailingBlobStore()
    _install(sink=sink, blob_store=failing, llm=_llm_caller)

    assert asyncio.run(invokeBrain(_brain_input())) == BRAIN_OUTPUT
    assert asyncio.run(runSub(_sub_input(), SUB_OUTPUT)) == SUB_OUTPUT

    steps = {s.op: s for s in sink.list_trajectory_steps(ROOT)}
    assert set(steps) == {"think", "sub"}
    for step in steps.values():
        assert step.input_ref is None
        assert step.output_ref is None
