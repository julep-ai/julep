from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any

import pytest

from julep import arr, each, par, race, seq
from julep.continuation import continue_with
from julep.execution import HAVE_TEMPORAL
from julep.execution.blobstore import InMemoryBlobStore
from julep.execution.effects import WorkerContext, configure, set_trajectory_sink
from julep.purity import register_pure
from julep.trajectory import (
    InMemoryTrajectoryStore,
    TrajectoryRun,
    TrajectoryStep,
    TrajectoryValue,
    trajectory_best_effort_failures,
)

if HAVE_TEMPORAL:
    from julep.execution import harness
    from julep.execution.harness import FlowInput, FlowWorkflow


ROOT = "tstruct-root"


def _double(v: Any) -> Any:
    return v * 2


def _inc(v: Any) -> Any:
    if isinstance(v, list):
        return [item + 1 for item in v]
    return v + 1


def _id(v: Any) -> Any:
    return v


def _fast(v: Any) -> Any:
    return v


def _slow(v: Any) -> Any:
    return {"slow": v}


def _continue_once(v: dict[str, Any]) -> Any:
    if isinstance(v, list):
        v = v[0]
    n = v.get("n", 0)
    if n < 1:
        return continue_with({"n": n + 1})
    return {"n": n, "done": True}


register_pure("tstruct.double", _double)
register_pure("tstruct.inc", _inc)
register_pure("tstruct.id", _id)
register_pure("tstruct.fast", _fast)
register_pure("tstruct.slow", _slow)
register_pure("tstruct.continue_once", _continue_once)

_PAR_EACH_FLOW = seq(each(arr("tstruct.double")), par(arr("tstruct.inc"), arr("tstruct.inc")))
_RACE_FLOW = race(arr("tstruct.fast"), arr("tstruct.slow"))
_CONTINUE_FLOW = seq(par(arr("tstruct.id"), arr("tstruct.id")), arr("tstruct.continue_once"))


class _Stop(Exception):
    """Raised by the fake continue_as_new to stop the segment chain."""


class _RaisingSink(InMemoryTrajectoryStore):
    def start_run(self, run: TrajectoryRun) -> None:
        raise RuntimeError("sink down: start_run")

    def append_steps(self, steps: list[TrajectoryStep]) -> None:
        raise RuntimeError("sink down: append_steps")

    def finish_run(self, run_id: str, status: str, finished_ts: float) -> None:
        raise RuntimeError("sink down: finish_run")

    def record_values(self, values: list[TrajectoryValue]) -> None:
        raise RuntimeError("sink down: record_values")


@pytest.fixture(autouse=True)
def _isolate_sink():
    set_trajectory_sink(None, None)
    yield
    set_trajectory_sink(None, None)


async def _mcp_call(
    server: str,
    tool: str,
    value: Any,
    key: str,
    principal: Any,
) -> Any:
    return {"ok": True, "value": value}


async def _llm(reasoner: Any, value: Any, principal: Any, transcript: Any) -> Any:
    return {"ok": True, "value": value}


def _configure_worker(sink: Any, blobs: InMemoryBlobStore) -> None:
    configure(WorkerContext(trajectory_sink=sink, trajectory_blob_store=blobs, mcp_call=_mcp_call, llm=_llm))


def _flow_input(flow_json: dict[str, Any], value: Any, *, session_id: str = ROOT) -> Any:
    return FlowInput(
        session_id=session_id,
        input=value,
        flow_json=flow_json,
        manifest_json={},
        max_call_limits={},
        root_run_id=session_id,
        segment_seq=0,
    )


def _flush_structural_impl() -> Any:
    wrapped = harness.flushStructural
    if hasattr(wrapped, "__wrapped__"):
        return wrapped.__wrapped__
    return inspect.unwrap(wrapped)


def _install_temporal_activity_stub(monkeypatch: pytest.MonkeyPatch, captured: list[dict[str, Any]]) -> None:
    flush_impl = _flush_structural_impl()

    async def fake_execute_activity(fn: Any, payload: Any = None, **kwargs: Any) -> Any:
        name = getattr(fn, "__name__", fn)
        if name == "flushStructural":
            captured.append(payload)
            return await flush_impl(payload)
        if name in {"startTrajectory", "finishTrajectory"}:
            return None
        if name in {"callTool", "invokeReasoner"}:
            return {"ok": True}
        return None

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)


def _structural_steps(sink: InMemoryTrajectoryStore, run_id: str = ROOT) -> list[TrajectoryStep]:
    return [step for step in sink.list_trajectory_steps(run_id) if step.kind in {"each", "par", "seq"}]


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_flush_structural_scrubs_run_secret_from_errors_and_attrs() -> None:
    sink = InMemoryTrajectoryStore()
    _configure_worker(sink, InMemoryBlobStore())
    asyncio.run(
        _flush_structural_impl()(
            {
                "runId": ROOT,
                "rootRunId": ROOT,
                "segmentSeq": 0,
                "nodeOps": {"node": "seq"},
                "secrets": {"token": "run-secret-value"},
                "events": [
                    {
                        "eventId": "event",
                        "type": "Failed",
                        "node": "node",
                        "cid": "cid",
                        "ts": 1.0,
                        "error": "failed with run-secret-value",
                        "attrs": {"detail": "echo=run-secret-value"},
                    }
                ],
            }
        )
    )

    [step] = sink.list_trajectory_steps(ROOT)
    assert "run-secret-value" not in str(step)
    assert step.error == "failed with [REDACTED]"
    assert step.attrs == {"detail": "echo=[REDACTED]"}


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_par_all_and_each_structural_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict[str, Any]] = []
    _install_temporal_activity_stub(monkeypatch, captured)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    out = asyncio.run(FlowWorkflow().run(_flow_input(_PAR_EACH_FLOW.to_json(), [1, 2, 3])))

    assert out == [[3, 5, 7], [3, 5, 7]]
    steps = _structural_steps(sink)
    each_steps = [step for step in steps if step.op == "each"]
    par_steps = [step for step in steps if step.op == "par"]
    assert len(each_steps) == 1
    assert each_steps[0].attrs["items"] == 3
    assert len(par_steps) == 1
    assert par_steps[0].attrs.get("merge") in (None, "all", "degraded")
    assert not any(step.op == "prim" for step in sink.list_trajectory_steps(ROOT))
    for step in each_steps + par_steps:
        assert step.input_ref is None
        assert step.output_ref is None


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_race_family_structural_step_has_winner_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, Any]] = []
    _install_temporal_activity_stub(monkeypatch, captured)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    out = asyncio.run(FlowWorkflow().run(_flow_input(_RACE_FLOW.to_json(), {"x": 1})))

    assert out == {"x": 1}
    par_steps = [step for step in sink.list_trajectory_steps(ROOT) if step.op == "par" and step.kind == "par"]
    assert len(par_steps) == 1
    step = par_steps[0]
    assert step.attrs["merge"] == "race"
    assert isinstance(step.attrs["winner"], int)
    assert isinstance(step.attrs["cancelled"], list)
    assert {"winner", "cancelled", "merge"}.issubset(step.attrs)


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_continue_as_new_flushes_segment_zero_structural_before_continuing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, Any]] = []
    _install_temporal_activity_stub(monkeypatch, captured)
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_worker(sink, blobs)

    def fake_continue_as_new(next_input: Any) -> None:
        raise _Stop()

    monkeypatch.setattr(harness.workflow, "continue_as_new", fake_continue_as_new)

    with pytest.raises(_Stop):
        asyncio.run(FlowWorkflow().run(_flow_input(_CONTINUE_FLOW.to_json(), {"n": 0})))

    assert captured
    assert captured[0]["segmentSeq"] == 0
    par_events = [
        event
        for payload in captured
        for event in payload["events"]
        if payload["nodeOps"].get(event["node"]) == "par"
    ]
    assert par_events
    par_steps = [step for step in sink.list_trajectory_steps(ROOT) if step.op == "par" and step.kind == "par"]
    assert len(par_steps) == 1


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_flow_result_byte_identical_when_flush_sink_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blobs = InMemoryBlobStore()

    def _run(sink: Any) -> Any:
        captured: list[dict[str, Any]] = []
        _install_temporal_activity_stub(monkeypatch, captured)
        _configure_worker(sink, blobs)
        return asyncio.run(FlowWorkflow().run(_flow_input(_PAR_EACH_FLOW.to_json(), [1, 2, 3])))

    baseline = _run(InMemoryTrajectoryStore())
    before = trajectory_best_effort_failures()
    with_failure = _run(_RaisingSink())
    set_trajectory_sink(None, None)

    assert trajectory_best_effort_failures() > before
    assert baseline == with_failure
    assert json.dumps(with_failure, sort_keys=True) == json.dumps(baseline, sort_keys=True)
