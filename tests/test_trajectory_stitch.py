"""Lane C (Stitching): run-identity threading + the terminal finish marker.

Where Lane B (``tests/test_trajectory_capture.py``) pins the per-effect capture
at the boundary, this lane pins how that capture is *stitched into a run*:

* a ``root_run_id`` (the root ``session_id``) and a ``segment_seq`` are threaded
  through the execution layer exactly like ``principal`` / ``call_counts`` —
  inherited by children, carried across ``continue_as_new`` / DBOS segments
  (``segment_seq`` increments, ``root_run_id`` stays constant);
* the run is lazily started on its first captured step and closed by ONE
  best-effort terminal finish marker (status + finished_ts, no payloads);
* NONE of this perturbs the run: capture lives only in the effect/sink layer, so
  a representative flow produces a byte-identical result AND an identical
  projection event stream whether the trajectory sink is installed or not, and a
  failing sink/finish-marker never changes the flow OR agent result (CRITICAL).

The determinism and best-effort tests run with NO Temporal/DBOS server. The
backend-specific threading tests monkeypatch the engine primitives (mirroring
``tests/test_run_principal.py``) so they too need no server; a test that would
genuinely require one is skipped when the engine is unavailable.
"""
from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any, Optional

import pytest

from julep import arr, call, each, mcp, native, seq, sub
from julep.continuation import continue_with
from julep.dotctx import Reasoner
from julep.registry import DEFAULT_REGISTRY
from julep.execution import HAVE_DBOS, HAVE_TEMPORAL
from julep.execution.blobstore import InMemoryBlobStore, parse_ref
from julep.execution.effects import (
    CallToolInput,
    WorkerContext,
    callTool,
    configure,
    set_trajectory_sink,
)
from julep.execution.interpreter import InMemoryEnv, interpret
from julep.projection import InMemoryProjection, ProjectionEmitter
from julep.purity import register_pure
from julep.trajectory import (
    InMemoryTrajectoryStore,
    TrajectoryRun,
    TrajectoryStep,
    TrajectoryValue,
    trajectory_best_effort_failures,
)

ROOT = "root-sess"


def _emitter() -> ProjectionEmitter:
    return ProjectionEmitter(InMemoryProjection())


@pytest.fixture(autouse=True)
def _isolate_sink():
    """Every test starts and ends with capture disabled (no leaked globals)."""
    set_trajectory_sink(None, None)
    yield
    set_trajectory_sink(None, None)


# --------------------------------------------------------------------------- #
# A representative flow, built ONCE so its node ids are stable across runs
# (node ids come from a process-global counter at construction time; building
# twice would shift them and is unrelated to the sink under test).
# --------------------------------------------------------------------------- #
register_pure("lcstitch.double", lambda v: v * 2)
register_pure("lcstitch.continue", lambda v: continue_with({"n": v.get("n", 0) + 1}))
_REPRESENTATIVE_FLOW = seq(call(native("echo")), arr("lcstitch.double"))


def _continue_until_two(v: dict[str, Any]) -> Any:
    """Continue for segments 0 and 1, then settle on segment 2 (n == 2)."""
    n = v.get("n", 0)
    if n >= 2:
        return {"n": n, "done": True}
    return continue_with({"n": n + 1})


register_pure("lcstitch.continue_until_two", _continue_until_two)


async def _mcp_caller(server: str, tool: str, value: Any, key: str, principal: Any) -> Any:
    return {"hits": value}


def test_capture_step_ids_include_segment_sequence_for_reused_cids():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    base = {
        "tool_ref": {"kind": "mcp", "server": "kb", "tool": "search"},
        "value": {"q": "same"},
        "cid": "shared-cid",
        "run_id": ROOT,
        "root_run_id": ROOT,
        "node_id": "search-node",
        "op": "call",
        "kind": "tool",
    }

    first = asyncio.run(callTool(CallToolInput(**base, segment_seq=0)))
    second = asyncio.run(callTool(CallToolInput(**base, segment_seq=1)))
    set_trajectory_sink(None, None)

    assert first == second == {"hits": {"q": "same"}}
    steps = sink.list_trajectory_steps(ROOT)
    assert len(steps) == 2
    assert len(sink._steps) == 2
    step_ids = [step.step_id for step in steps]
    assert len(set(step_ids)) == 2
    assert any(":s0:" in step_id for step_id in step_ids)
    assert any(":s1:" in step_id for step_id in step_ids)


# --------------------------------------------------------------------------- #
# CRITICAL determinism (golden-hash): sink installed vs not-installed produces a
# byte-identical terminal result AND an identical projection event stream.
# --------------------------------------------------------------------------- #
def _run_representative(install_sink: bool) -> tuple[Any, list[dict[str, Any]]]:
    store = InMemoryProjection()
    emitter = ProjectionEmitter(store)
    env = InMemoryEnv(
        {},
        emitter,
        tools={"echo": lambda v: v + 1},
        root_run_id=ROOT,
        segment_seq=0,
    )
    set_trajectory_sink(
        InMemoryTrajectoryStore() if install_sink else None,
        InMemoryBlobStore() if install_sink else None,
    )
    try:
        result = asyncio.run(interpret(_REPRESENTATIVE_FLOW, 5, env))
    finally:
        set_trajectory_sink(None, None)
    return result.value, [e.to_json() for e in store.events()]


def test_determinism_sink_install_does_not_change_result_or_projection():
    """Trajectory capture must live only in the effect/sink layer: installing the
    process-global sink changes neither interpret()'s value nor its pomset."""
    value_off, events_off = _run_representative(install_sink=False)
    value_on, events_on = _run_representative(install_sink=True)

    # Byte-identical terminal result.
    assert value_on == value_off == 12
    assert json.dumps(value_on, sort_keys=True) == json.dumps(value_off, sort_keys=True)

    # Identical projection event stream (golden-hash over the whole pomset).
    assert json.dumps(events_on, sort_keys=True) == json.dumps(events_off, sort_keys=True)


def test_interpret_installs_run_identity_onto_env():
    """interpret(root_run_id=..., segment_seq=...) installs onto the env once,
    like principal; the interpreter itself never reads them back."""
    env = InMemoryEnv({}, _emitter(), tools={"echo": lambda v: v})
    assert env.root_run_id is None
    assert env.segment_seq == 0
    asyncio.run(
        interpret(call(native("echo")), 5, env, root_run_id="adopted", segment_seq=3)
    )
    assert env.root_run_id == "adopted"
    assert env.segment_seq == 3


# --------------------------------------------------------------------------- #
# Temporal: continue_as_new keeps root_run_id and increments segment_seq; the
# finish marker fires only on settlement, never on continuation; children inherit
# the root. All without a server (engine primitives monkeypatched).
# --------------------------------------------------------------------------- #
if HAVE_TEMPORAL:
    from julep.execution import harness
    from julep.execution.harness import (
        AgentInput,
        AgentWorkflow,
        FlowInput,
        FlowWorkflow,
        _TemporalEnv,
    )
    from julep.execution.policy import ExecutionPolicy


class _Stop(Exception):
    """Raised by the fake continue_as_new to capture the next segment's input."""


def _temporal_env(
    *,
    root_run_id: Optional[str],
    segment_seq: int = 0,
    runtime_declarations_ref: Optional[dict[str, Any]] = None,
) -> Any:
    async def gate(value: Any, cid: str, timeout_s: Optional[int]) -> Any:
        return value

    return _TemporalEnv(
        manifest={},
        emitter=_emitter(),
        session_id="seg-sess",
        manifest_json={},
        policy=ExecutionPolicy(),
        gate_waiter=gate,
        root_run_id=root_run_id,
        segment_seq=segment_seq,
        runtime_declarations_ref=runtime_declarations_ref,
    )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_env_stamps_run_identity_into_effect_payloads(monkeypatch):
    payloads: list[Any] = []

    async def fake_execute_activity(fn, payload, **kwargs):
        payloads.append(payload)
        return {"ok": True}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    env = _temporal_env(root_run_id=ROOT, segment_seq=2)

    asyncio.run(env.run_call(call(mcp("kb", "search")), {"q": "x"}, "cid-1"))
    asyncio.run(env.invoke_reasoner("b", 5, "cid-2", None))

    # invoke_reasoner now records the resolved QoS tier via a resolveQoS activity
    # before the sync invokeReasoner dispatch, so the reasoner leg yields two payloads.
    tool = next(p for p in payloads if getattr(p, "kind", None) == "tool")
    reasoner = next(p for p in payloads if getattr(p, "kind", None) == "reasoner")
    # run_id is this segment's session; root_run_id + segment_seq are the run identity.
    assert tool.run_id == "seg-sess"
    assert tool.root_run_id == ROOT and tool.segment_seq == 2
    assert tool.op == "call" and tool.kind == "tool"
    assert reasoner.root_run_id == ROOT and reasoner.segment_seq == 2
    assert reasoner.op == "think" and reasoner.kind == "reasoner"


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_children_inherit_root_run_id(monkeypatch):
    children: list[Any] = []
    declarations_ref = {"hash": "sha256:" + "a" * 64, "size": 123}

    async def fake_execute_child_workflow(fn, child_input, **kwargs):
        children.append(child_input)
        return "child-result"

    monkeypatch.setattr(
        harness.workflow, "execute_child_workflow", fake_execute_child_workflow
    )
    env = _temporal_env(
        root_run_id=ROOT,
        segment_seq=4,
        runtime_declarations_ref=declarations_ref,
    )

    asyncio.run(env.run_sub("child", None, 5, "cid-1"))
    asyncio.run(env.run_agent("lcstitch.ctrl", 5, "cid-2"))

    sub_input, agent_input = children
    # Children inherit the SAME root; they begin their own segment chain at 0.
    assert isinstance(sub_input, FlowInput)
    assert sub_input.root_run_id == ROOT and sub_input.segment_seq == 0
    # A ref child resolves its own pipeline declarations instead of inheriting
    # the parent's per-pipeline blob.
    assert sub_input.runtime_declarations_ref is None
    assert isinstance(agent_input, AgentInput)
    assert agent_input.root_run_id == ROOT and agent_input.segment_seq == 0
    assert agent_input.runtime_declarations_ref == declarations_ref


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_continue_as_new_keeps_root_and_increments_segment(monkeypatch):
    captured: list[Any] = []
    finishes: list[Any] = []
    declarations_ref = {"hash": "sha256:" + "b" * 64, "size": 456}

    def fake_continue_as_new(next_input):
        captured.append(next_input)
        raise _Stop()

    async def fake_execute_activity(fn, payload, **kwargs):
        finishes.append((getattr(fn, "__name__", fn), payload))
        return None

    monkeypatch.setattr(harness.workflow, "continue_as_new", fake_continue_as_new)
    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)

    # A run dispatched with no root adopts its own session_id as root_run_id.
    inp = FlowInput(
        session_id=ROOT,
        input={"n": 0},
        flow_json=arr("lcstitch.continue").to_json(),
        manifest_json={},
        max_call_limits={},
        root_run_id=None,
        segment_seq=0,
        runtime_declarations_ref=declarations_ref,
    )
    with pytest.raises(_Stop):
        asyncio.run(FlowWorkflow().run(inp))

    (next_input,) = captured
    assert isinstance(next_input, FlowInput)
    assert next_input.root_run_id == ROOT  # constant across the chain
    assert next_input.segment_seq == 1     # bumped for the next segment
    assert next_input.input == {"n": 1}
    assert next_input.runtime_declarations_ref == declarations_ref
    # A continued segment is NOT settled: the finish marker must not fire.
    finish_names = [name for name, _ in finishes if name == "finishTrajectory"]
    assert finish_names == []
    assert [name for name, _ in finishes if name == "startTrajectory"] == [
        "startTrajectory"
    ]


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_settlement_fires_finish_marker_once(monkeypatch):
    finishes: list[Any] = []

    async def fake_execute_activity(fn, payload, **kwargs):
        if getattr(fn, "__name__", "") == "finishTrajectory":
            finishes.append(payload)
            return None
        return {"hits": 1}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)

    inp = FlowInput(
        session_id=ROOT,
        input=5,
        flow_json=call(mcp("kb", "search")).to_json(),
        manifest_json={},
        max_call_limits={},
    )
    out = asyncio.run(FlowWorkflow().run(inp))

    assert out == {"hits": 1}
    # Exactly one terminal marker, addressed to the root run (runId == rootRunId
    # for a root flow), with the final value.
    assert finishes == [
        {
            "runId": ROOT,
            "rootRunId": ROOT,
            "status": "completed",
            "result": {"hits": 1},
            "segmentSeq": 0,
        }
    ]


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_child_finishes_own_run_not_root(monkeypatch):
    # F1 regression (the blind spot that let the bug through): a child flow
    # (root_run_id != session_id) must finish ITS OWN run, stitched to the root
    # via rootRunId -- never finish/overwrite the ROOT run with the child's
    # result. Before the fix, the child's terminal marker targeted runId=ROOT,
    # so the root run's "final" became a child's output.
    finishes: list[Any] = []

    async def fake_execute_activity(fn, payload, **kwargs):
        if getattr(fn, "__name__", "") == "finishTrajectory":
            finishes.append(payload)
            return None
        return {"hits": 1}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)

    child = "child-sess"
    inp = FlowInput(
        session_id=child,
        input=5,
        flow_json=call(mcp("kb", "search")).to_json(),
        manifest_json={},
        max_call_limits={},
        root_run_id=ROOT,
        segment_seq=0,
    )
    asyncio.run(FlowWorkflow().run(inp))

    # Finishes the CHILD run, stitched to ROOT -- the root run is untouched.
    assert finishes == [
        {
            "runId": child,
            "rootRunId": ROOT,
            "status": "completed",
            "result": {"hits": 1},
            "segmentSeq": 0,
        }
    ]
    assert all(p["runId"] != ROOT for p in finishes)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_result_byte_identical_when_finish_marker_raises(monkeypatch):
    """CRITICAL: a failing terminal finish marker leaves the flow result
    byte-identical (best-effort; never raises into the run)."""

    async def good_execute_activity(fn, payload, **kwargs):
        if getattr(fn, "__name__", "") == "finishTrajectory":
            return None
        return {"hits": 7}

    async def bad_execute_activity(fn, payload, **kwargs):
        if getattr(fn, "__name__", "") == "finishTrajectory":
            raise RuntimeError("trajectory marker activity down")
        return {"hits": 7}

    def _run(execute):
        monkeypatch.setattr(harness.workflow, "execute_activity", execute)
        inp = FlowInput(
            session_id=ROOT,
            input=5,
            flow_json=call(mcp("kb", "search")).to_json(),
            manifest_json={},
            max_call_limits={},
        )
        return asyncio.run(FlowWorkflow().run(inp))

    baseline = _run(good_execute_activity)
    with_failure = _run(bad_execute_activity)
    assert baseline == with_failure == {"hits": 7}
    assert json.dumps(with_failure, sort_keys=True) == json.dumps(baseline, sort_keys=True)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flow_finish_activity_dispatch_failure_is_swallowed(monkeypatch):
    # A finish-activity DISPATCH failure (execute_activity raises) is swallowed
    # and logged via stdlib logging -- NOT counted, because mutating the
    # module-global best-effort counter from replayable workflow code would
    # inflate it on every replay. Genuine trajectory-write failures
    # *inside* the activity (a raising sink) are still counted; that replay-safe
    # path is covered by the sink-failure counter tests in this module. The
    # invariant asserted here is the one that matters: the run is never affected.
    async def bad_execute_activity(fn, payload, **kwargs):
        raise RuntimeError("trajectory marker activity down")

    monkeypatch.setattr(harness.workflow, "execute_activity", bad_execute_activity)
    set_trajectory_sink(InMemoryTrajectoryStore(), InMemoryBlobStore())

    # Swallowed: no raise, returns None -- the workflow continues unaffected.
    assert asyncio.run(FlowWorkflow()._finish_trajectory("some-run")) is None


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_agent_continue_as_new_keeps_root_and_increments_segment(monkeypatch):
    captured: list[Any] = []

    async def fake_execute_activity(fn, payload, **kwargs):
        if getattr(fn, "__name__", "") == "invokeReasoner":
            return {"tool": "t", "input": 1}
        return {"tool": "out"}

    def fake_continue_as_new(next_input):
        captured.append(next_input)
        raise _Stop()

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    monkeypatch.setattr(harness.workflow, "continue_as_new", fake_continue_as_new)

    inp = AgentInput(
        controller="lcstitch.ctrl",
        session_id=ROOT,
        input=5,
        config={"maxRounds": 5, "budget": {"cost": 1000}, "continueAsNewAfter": 1},
        resolve_spec=False,
        root_run_id=None,
        segment_seq=0,
    )
    with pytest.raises(_Stop):
        asyncio.run(AgentWorkflow().run(inp))

    (next_input,) = captured
    assert isinstance(next_input, AgentInput)
    assert next_input.root_run_id == ROOT
    assert next_input.segment_seq == 1


# --------------------------------------------------------------------------- #
# DBOS: one root_run_id across the segment chain; controller turns + CALL/SUB
# captured; parent_run_id on child runs surfaces via include_children; the
# terminal finish marker fires once at settlement and is best-effort. No server.
# --------------------------------------------------------------------------- #
if HAVE_DBOS:
    from julep.execution import dbos_backend
    from julep.execution.dbos_backend import run_agent_dbos, run_flow_dbos


class _NoopSetWorkflowID:
    def __init__(self, wfid: str) -> None:
        pass

    def __enter__(self) -> "_NoopSetWorkflowID":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


def _install_inline_dbos(monkeypatch, *, body) -> list[dict[str, Any]]:
    """Run DBOS segments inline (no server): start_workflow_async invokes the
    unwrapped workflow body directly. Returns the list of submitted payloads."""
    submitted: list[dict[str, Any]] = []
    unwrapped = inspect.unwrap(body)

    class _Handle:
        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        async def get_result(self) -> Any:
            return await unwrapped(self._payload)

    class _FakeDBOS:
        @staticmethod
        async def start_workflow_async(fn, payload):
            submitted.append(payload)
            return _Handle(payload)

    monkeypatch.setattr(dbos_backend, "DBOS", _FakeDBOS)
    monkeypatch.setattr(dbos_backend, "SetWorkflowID", _NoopSetWorkflowID)
    return submitted


def _configure_worker(sink, blobs, **extra) -> None:
    configure(
        WorkerContext(
            mcp_call=_mcp_caller,
            blob_store=blobs,
            trajectory_sink=sink,
            trajectory_blob_store=blobs,
            **extra,
        )
    )


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_flow_chain_shares_one_root_run_id(monkeypatch):
    submitted = _install_inline_dbos(monkeypatch, body=dbos_backend.flow_workflow)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    # Continues for segments 0 and 1, settles on segment 2.
    out = asyncio.run(
        run_flow_dbos(
            arr("lcstitch.continue_until_two").to_json(),
            {},
            session_id=ROOT,
            input={"n": 0},
            max_segments=10,
        )
    )
    set_trajectory_sink(None, None)

    assert out == {"n": 2, "done": True}
    # Three segments were submitted: one root_run_id, segment_seq == index.
    assert len(submitted) == 3
    assert all(p["rootRunId"] == ROOT for p in submitted)
    assert [p["segmentSeq"] for p in submitted] == [0, 1, 2]
    # seg 0 runs under the base id; later segments are suffixed.
    assert submitted[0]["sessionId"] == ROOT
    assert submitted[1]["sessionId"] == f"{ROOT}-seg1"


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_flow_settlement_finishes_run(monkeypatch):
    _install_inline_dbos(monkeypatch, body=dbos_backend.flow_workflow)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    out = asyncio.run(
        run_flow_dbos(
            call(mcp("kb", "search")).to_json(),
            {},
            session_id=ROOT,
            input=5,
        )
    )
    set_trajectory_sink(None, None)

    assert out == {"hits": 5}
    # Root marker, CALL leaf, and final marker were captured under the root run.
    steps = sink.list_trajectory_steps(ROOT, include_children=True)
    assert {(s.op, s.kind, s.run_id) for s in steps} == {
        ("root", "root", ROOT),
        ("call", "tool", ROOT),
        ("final", "final", ROOT),
    }
    assert ("call", "tool", ROOT) in {(s.op, s.kind, s.run_id) for s in steps}
    run = sink.get_trajectory_run(ROOT)
    assert run is not None
    assert run.status == "completed"
    assert run.finished_ts is not None


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_agent_captures_turns_and_child_subflow(monkeypatch):
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="lcstitch.ctrl", model="test", system="s"))
    _install_inline_dbos(monkeypatch, body=dbos_backend.agent_workflow)

    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    replies = iter([{"sub": "child", "input": 1}, {"output": {"ok": 1}}])

    async def llm(reasoner: Any, value: Any, principal: Any, transcript: Any) -> Any:
        return next(replies)

    configure(
        WorkerContext(
            mcp_call=_mcp_caller,
            llm=llm,
            blob_store=blobs,
            trajectory_sink=sink,
            trajectory_blob_store=blobs,
            subflows={
                "child": {"flowJson": call(mcp("kb", "search")).to_json(), "manifestJson": {}}
            },
            agents={
                "lcstitch.ctrl": {
                    "config": {"maxRounds": 5, "budget": {"cost": 1000}},
                    "grantedSubflows": ["child"],
                }
            },
        )
    )

    out = asyncio.run(run_agent_dbos("lcstitch.ctrl", session_id=ROOT, input=5))
    set_trajectory_sink(None, None)

    assert out["status"] == "done" and out["output"] == {"ok": 1}

    # include_children=True stitches the child sub-flow's steps into the root run.
    child_steps = sink.list_trajectory_steps(ROOT, include_children=True)
    ops = [(s.op, s.run_id) for s in child_steps]
    assert ("think", ROOT) in ops                 # controller turns captured
    assert ("call", f"{ROOT}-sub-0") in ops       # CALL inside the child sub-flow

    # Without children, only the root run's own steps are returned.
    root_only = sink.list_trajectory_steps(ROOT, include_children=False)
    assert all(s.run_id == ROOT for s in root_only)
    assert all(s.run_id != f"{ROOT}-sub-0" for s in root_only)

    # parent_run_id is set on the child sub run; the root finished once.
    child_run = sink.get_trajectory_run(f"{ROOT}-sub-0")
    assert child_run is not None
    assert child_run.parent_run_id == ROOT
    assert child_run.root_run_id == ROOT
    root_run = sink.get_trajectory_run(ROOT)
    assert root_run is not None and root_run.status == "completed"


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_subflow_capture_records_flow_step(monkeypatch):
    _install_inline_dbos(monkeypatch, body=dbos_backend.flow_workflow)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(
        sink,
        blobs,
        subflows={
            "child": {"flowJson": call(mcp("kb", "search")).to_json(), "manifestJson": {}}
        },
    )

    out = asyncio.run(
        run_flow_dbos(
            sub("child").to_json(),
            {},
            session_id=ROOT,
            input=5,
        )
    )
    set_trajectory_sink(None, None)

    assert out == {"hits": 5}
    steps = sink.list_trajectory_steps(ROOT, include_children=True)
    assert any(s.op == "sub" and s.kind == "flow" and s.run_id == ROOT for s in steps)

    child_calls = [
        s for s in steps if s.op == "call" and s.kind == "tool" and s.run_id != ROOT
    ]
    assert len(child_calls) == 1
    child_run = sink.get_trajectory_run(child_calls[0].run_id)
    assert child_run is not None
    assert child_run.parent_run_id == ROOT
    assert child_run.root_run_id == ROOT


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_par_each_structural_steps_sourced_from_projection(monkeypatch):
    _install_inline_dbos(monkeypatch, body=dbos_backend.flow_workflow)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    out = asyncio.run(
        run_flow_dbos(
            each(arr("lcstitch.double")).to_json(),
            {},
            session_id=ROOT,
            input=[1, 2, 3],
        )
    )
    set_trajectory_sink(None, None)

    assert out == [2, 4, 6]
    structural = [
        s for s in sink.list_trajectory_steps(ROOT) if s.op == "each" and s.kind == "each"
    ]
    assert len(structural) == 1
    assert structural[0].attrs["items"] == 3
    assert structural[0].input_ref is None
    assert structural[0].output_ref is None


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_root_and_final_markers_recorded(monkeypatch):
    _install_inline_dbos(monkeypatch, body=dbos_backend.flow_workflow)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    root_input = {"q": "needle"}
    out = asyncio.run(
        run_flow_dbos(
            call(mcp("kb", "search")).to_json(),
            {},
            session_id=ROOT,
            input=root_input,
        )
    )
    set_trajectory_sink(None, None)

    assert out == {"hits": root_input}
    steps = sink.list_trajectory_steps(ROOT, include_children=False)
    root_steps = [s for s in steps if s.kind == "root"]
    final_steps = [s for s in steps if s.kind == "final"]
    assert len(root_steps) == 1
    assert len(final_steps) == 1

    root_step = root_steps[0]
    final_step = final_steps[0]
    assert root_step.input_ref is not None and root_step.output_ref is None
    assert final_step.output_ref is not None and final_step.input_ref is None
    root_tenant, _ = parse_ref(root_step.input_ref)
    final_tenant, _ = parse_ref(final_step.output_ref)
    assert root_tenant == final_tenant == ROOT
    assert asyncio.run(blobs.get(ROOT, root_step.input_ref)) == json.dumps(
        root_input, sort_keys=True
    ).encode()
    assert asyncio.run(blobs.get(ROOT, final_step.output_ref)) == json.dumps(
        out, sort_keys=True
    ).encode()

    values = sink.list_trajectory_values(ROOT)
    assert {v.kind: v.ref for v in values if v.step_id in {root_step.step_id, final_step.step_id}} == {
        "input": root_step.input_ref,
        "output": final_step.output_ref,
    }


# --------------------------------------------------------------------------- #
# Best-effort at the stitching level: a failing sink leaves BOTH the flow result
# and the agent result byte-identical (CRITICAL). No server.
# --------------------------------------------------------------------------- #
class _RaisingSink(InMemoryTrajectoryStore):
    def start_run(self, run: TrajectoryRun) -> None:
        raise RuntimeError("sink down: start_run")

    def append_steps(self, steps: list[TrajectoryStep]) -> None:
        raise RuntimeError("sink down: append_steps")

    def finish_run(self, run_id: str, status: str, finished_ts: float) -> None:
        raise RuntimeError("sink down: finish_run")

    def record_values(self, values: list[TrajectoryValue]) -> None:
        raise RuntimeError("sink down: record_values")


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_flow_result_byte_identical_when_sink_raises(monkeypatch):
    _install_inline_dbos(monkeypatch, body=dbos_backend.flow_workflow)
    blobs = InMemoryBlobStore()
    flow_json = call(mcp("kb", "search")).to_json()

    _configure_worker(InMemoryTrajectoryStore(), blobs)
    baseline = asyncio.run(run_flow_dbos(flow_json, {}, session_id=ROOT, input=5))

    before = trajectory_best_effort_failures()
    _configure_worker(_RaisingSink(), blobs)
    with_failure = asyncio.run(run_flow_dbos(flow_json, {}, session_id=ROOT, input=5))
    set_trajectory_sink(None, None)

    # CRITICAL: the run never sees the sink failure.
    assert baseline == with_failure == {"hits": 5}
    assert json.dumps(with_failure, sort_keys=True) == json.dumps(baseline, sort_keys=True)
    # The failures were swallowed + counted (start_run, append_steps, finish_run).
    assert trajectory_best_effort_failures() > before


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_flow_result_byte_identical_when_finish_step_raises(monkeypatch):
    _install_inline_dbos(monkeypatch, body=dbos_backend.flow_workflow)
    blobs = InMemoryBlobStore()
    flow_json = call(mcp("kb", "search")).to_json()

    _configure_worker(InMemoryTrajectoryStore(), blobs)
    baseline = asyncio.run(run_flow_dbos(flow_json, {}, session_id=ROOT, input=5))

    async def bad_finish_step(inp: dict[str, Any]) -> None:
        raise RuntimeError("trajectory marker step down")

    before = trajectory_best_effort_failures()
    monkeypatch.setattr(dbos_backend, "finishTrajectoryStep", bad_finish_step)
    _configure_worker(InMemoryTrajectoryStore(), blobs)
    with_failure = asyncio.run(run_flow_dbos(flow_json, {}, session_id=ROOT, input=5))
    set_trajectory_sink(None, None)

    assert baseline == with_failure == {"hits": 5}
    assert json.dumps(with_failure, sort_keys=True) == json.dumps(baseline, sort_keys=True)
    assert trajectory_best_effort_failures() > before


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_agent_result_byte_identical_when_sink_raises(monkeypatch):
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="lcstitch.ctrl", model="test", system="s"))
    _install_inline_dbos(monkeypatch, body=dbos_backend.agent_workflow)
    blobs = InMemoryBlobStore()

    def _agent(sink) -> dict[str, Any]:
        replies = iter([{"output": {"ok": 2}}])

        async def llm(reasoner: Any, value: Any, principal: Any, transcript: Any) -> Any:
            return next(replies)

        configure(
            WorkerContext(
                llm=llm,
                blob_store=blobs,
                trajectory_sink=sink,
                trajectory_blob_store=blobs,
                agents={
                    "lcstitch.ctrl": {
                        "config": {"maxRounds": 5, "budget": {"cost": 1000}}
                    }
                },
            )
        )
        return asyncio.run(run_agent_dbos("lcstitch.ctrl", session_id=ROOT, input=5))

    baseline = _agent(InMemoryTrajectoryStore())
    with_failure = _agent(_RaisingSink())
    set_trajectory_sink(None, None)

    assert baseline["status"] == with_failure["status"] == "done"
    assert baseline["output"] == with_failure["output"] == {"ok": 2}
    assert json.dumps(with_failure, sort_keys=True) == json.dumps(baseline, sort_keys=True)


@pytest.mark.skipif(not HAVE_DBOS, reason="dbos not installed")
def test_dbos_child_agent_chain_finishes_own_run_not_root(monkeypatch):
    # F1 (DBOS Op.APP variant): a child agent chain inherits rootRunId from its
    # parent (DbosEnv.run_agent), but must finish ITS OWN run (base_id), stitched
    # to the root via rootRunId -- never overwrite the root run's final with the
    # child agent's result.
    finishes: list[dict[str, Any]] = []

    async def fake_finish(inp: dict[str, Any]) -> None:
        finishes.append(inp)

    async def fake_start(inp: dict[str, Any]) -> None:
        pass

    terminal = {"status": "done", "output": "child-out"}

    class _Handle:
        async def get_result(self) -> Any:
            return terminal

    class _FakeDBOS:
        @staticmethod
        async def start_workflow_async(fn, payload):
            return _Handle()

    monkeypatch.setattr(dbos_backend, "finishTrajectoryStep", fake_finish)
    monkeypatch.setattr(dbos_backend, "startTrajectoryStep", fake_start)
    monkeypatch.setattr(dbos_backend, "DBOS", _FakeDBOS)
    monkeypatch.setattr(dbos_backend, "SetWorkflowID", _NoopSetWorkflowID)

    base_id = f"{ROOT}-agent-1"
    payload = {
        "controller": "c",
        "sessionId": base_id,
        "input": 5,
        "rootRunId": ROOT,  # inherited from the parent flow's Op.APP node
        "segmentSeq": 0,
    }
    out = asyncio.run(dbos_backend._run_agent_chain(payload, base_id=base_id))

    assert out == terminal
    # Finishes the child's OWN run, stitched to ROOT -- the root run is untouched.
    assert finishes == [
        {
            "runId": base_id,
            "rootRunId": ROOT,
            "status": "completed",
            "finalValue": terminal,
            "segmentSeq": 0,
        }
    ]
    assert all(f["runId"] != ROOT for f in finishes)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_agent_sub_action_captured(monkeypatch):
    # Parity fix: an agent-loop SUB action records a sub/flow trajectory step via
    # runSubCapture, matching FlowWorkflow's SubStep and the DBOS backend. Before
    # the fix, AgentWorkflow's SUB branch recorded only the legacy TraceEntry, so
    # Temporal agent trajectories lost the parent sub step + input/output edge.
    sub_captures: list[dict[str, Any]] = []

    async def fake_execute_activity(fn, *a, **kw):
        name = getattr(fn, "__name__", "")
        if name == "invokeReasoner":
            return {"sub": "child", "input": 7}
        if name == "runSubCapture":
            captured = kw.get("args") or list(a)
            sub_captures.append(captured[0])
            return None
        return None

    async def fake_execute_child_workflow(fn, child_input, **kwargs):
        return {"child": "done"}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    monkeypatch.setattr(
        harness.workflow, "execute_child_workflow", fake_execute_child_workflow
    )

    inp = AgentInput(
        controller="ctrl",
        session_id=ROOT,
        input=5,
        config={"maxRounds": 1, "budget": {"cost": 1000}},
        granted_subflows=["child"],
        resolve_spec=False,
    )
    asyncio.run(AgentWorkflow().run(inp))

    assert len(sub_captures) == 1
    cap = sub_captures[0]
    assert cap["ref"] == "child"
    assert cap["op"] == "sub" and cap["kind"] == "flow"
    assert cap["run_id"] == ROOT and cap["root_run_id"] == ROOT
