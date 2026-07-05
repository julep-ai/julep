"""Server-free determinism gate for the trajectory plane.

Capture ON vs OFF must produce an identical result and identical projection.
The interpreter-level test proves sink installation is observational there; the
effect-level tests drive real capture writes directly, without Temporal/DBOS.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import pytest

from julep import arr, call, native, seq
from julep.dotctx import Reasoner
from julep.registry import DEFAULT_REGISTRY
from julep.execution.blobstore import InMemoryBlobStore
from julep.execution.effects import (
    CallToolInput,
    InvokeReasonerInput,
    WorkerContext,
    callTool,
    configure,
    invokeReasoner,
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

ROOT = "detm-root"
RUN = "detm-run"

CALL_INPUT = {"q": "determinism"}
CALL_OUTPUT = {"hits": [1, 2, 3], "ok": True}
REASONER_INPUT = {"prompt": "summarize deterministically"}
REASONER_OUTPUT = {"reply": "fixed", "tokens": 7}


register_pure("detm.double", lambda v: v * 2)
DEFAULT_REGISTRY.register_reasoner(Reasoner(name="detm.reasoner", model="test", system="s"))
_REPRESENTATIVE_FLOW = seq(call(native("echo")), arr("detm.double"))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _install(
    *,
    sink: Optional[InMemoryTrajectoryStore],
    blob_store: Optional[InMemoryBlobStore],
) -> None:
    configure(
        WorkerContext(
            mcp_call=_mcp_caller,
            llm=_llm_caller,
            blob_store=blob_store,
            trajectory_sink=sink,
            trajectory_blob_store=blob_store,
        )
    )
    set_trajectory_sink(sink, blob_store)


@pytest.fixture(autouse=True)
def _isolate_sink():
    """Every test starts and ends with capture disabled (no leaked globals)."""
    set_trajectory_sink(None, None)
    yield
    set_trajectory_sink(None, None)


async def _mcp_caller(
    server: str, tool: str, value: Any, key: str, principal: Any
) -> Any:
    return CALL_OUTPUT


async def _llm_caller(
    reasoner: Any, value: Any, principal: Any, transcript: Any
) -> Any:
    return REASONER_OUTPUT


def _tool_input() -> CallToolInput:
    return CallToolInput(
        tool_ref={"kind": "mcp", "server": "detm", "tool": "search"},
        value=CALL_INPUT,
        cid="detm-call-cid",
        run_id=RUN,
        root_run_id=ROOT,
        segment_seq=0,
        node_id="detm-call-node",
        op="call",
        kind="tool",
        causes=("detm-upstream",),
    )


def _reasoner_input() -> InvokeReasonerInput:
    return InvokeReasonerInput(
        reasoner="detm.reasoner",
        value=REASONER_INPUT,
        cid="detm-reasoner-cid",
        run_id=RUN,
        root_run_id=ROOT,
        segment_seq=0,
        node_id="detm-reasoner-node",
        op="think",
        kind="reasoner",
        causes=("detm-upstream",),
    )


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


def test_interpret_capture_on_off_identical_result_and_projection():
    value_on, events_on = _run_representative(install_sink=True)
    value_off, events_off = _run_representative(install_sink=False)

    assert value_on == value_off == 12
    assert _canonical_json(value_on) == _canonical_json(value_off)
    assert _canonical_json(events_on) == _canonical_json(events_off)


def test_effect_capture_on_off_result_byte_identical():
    cases = [
        (
            "callTool",
            lambda: asyncio.run(callTool(_tool_input())),
            CALL_OUTPUT,
        ),
        (
            "invokeReasoner",
            lambda: asyncio.run(invokeReasoner(_reasoner_input())),
            REASONER_OUTPUT,
        ),
    ]

    for name, run_effect, expected in cases:
        sink = InMemoryTrajectoryStore()
        blobs = InMemoryBlobStore()
        _install(sink=sink, blob_store=blobs)
        value_on = run_effect()
        steps = sink.list_trajectory_steps(ROOT, include_children=True)

        _install(sink=None, blob_store=InMemoryBlobStore())
        value_off = run_effect()

        assert value_on == value_off == expected, name
        assert _canonical_json(value_on) == _canonical_json(value_off), name
        assert steps, name


class _RaisingSink(InMemoryTrajectoryStore):
    def start_run(self, run: TrajectoryRun) -> None:
        raise RuntimeError("sink down: start_run")

    def append_steps(self, steps: list[TrajectoryStep]) -> None:
        raise RuntimeError("sink down: append_steps")

    def record_values(self, values: list[TrajectoryValue]) -> None:
        raise RuntimeError("sink down: record_values")


def test_failing_sink_keeps_effect_result_byte_identical():
    blobs = InMemoryBlobStore()
    good = InMemoryTrajectoryStore()
    _install(sink=good, blob_store=blobs)
    baseline = asyncio.run(callTool(_tool_input()))

    before = trajectory_best_effort_failures()
    bad = _RaisingSink()
    _install(sink=bad, blob_store=blobs)
    result = asyncio.run(callTool(_tool_input()))

    assert result == baseline == CALL_OUTPUT
    assert _canonical_json(result) == _canonical_json(baseline)
    assert trajectory_best_effort_failures() > before
