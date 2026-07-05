"""Trajectory capture redaction tests."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any, Callable, Optional

import pytest

from julep.dotctx import Reasoner
from julep.execution.blobstore import InMemoryBlobStore
from julep.execution.effects import (
    CallToolInput,
    InvokeReasonerInput,
    WorkerContext,
    callTool,
    configure,
    invokeReasoner,
    record_marker_step,
    set_trajectory_sink,
)
from julep.registry import DEFAULT_REGISTRY
from julep.trajectory import (
    REDACTED_PLACEHOLDER,
    InMemoryTrajectoryStore,
    TrajectoryRecorder,
    TrajectoryRun,
    TrajectoryStep,
    TrajectoryValue,
    redact_secret_shaped,
    trajectory_best_effort_failures,
)

ROOT = "run-root"
RUN = "run-root"
REASONER = "redaction.reasoner"


@pytest.fixture(autouse=True)
def _isolate_capture() -> None:
    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(name=REASONER, model="test", system="test")
    )
    set_trajectory_sink(None, None)
    yield
    set_trajectory_sink(None, None)
    configure(WorkerContext())


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True).encode()


async def _mcp_ok(
    server: str,
    tool: str,
    value: Any,
    key: str,
    principal: Any,
) -> dict[str, Any]:
    return {"ok": True, "seen": value.get("q") if isinstance(value, dict) else None}


async def _llm_ok(
    reasoner: Any,
    value: Any,
    principal: Any,
    transcript: Any,
    dispatch: Any,
) -> dict[str, Any]:
    return {"ok": "reasoned", "seen": value.get("brief_id") if isinstance(value, dict) else None}


def _tool_input(value: Any, cid: str = "call-redact") -> CallToolInput:
    return CallToolInput(
        tool_ref={"kind": "mcp", "server": "kb", "tool": "search"},
        value=value,
        cid=cid,
        run_id=RUN,
        root_run_id=ROOT,
        segment_seq=0,
        node_id="search-node",
        op="call",
        kind="tool",
        causes=("up-1",),
    )


def _reasoner_input(value: Any, cid: str = "think-redact") -> InvokeReasonerInput:
    return InvokeReasonerInput(
        reasoner=REASONER,
        value=value,
        cid=cid,
        run_id=RUN,
        root_run_id=ROOT,
        segment_seq=0,
        node_id="think-node",
        op="think",
        kind="reasoner",
        causes=("up-2",),
    )


def _configure_capture(
    *,
    sink: InMemoryTrajectoryStore,
    blobs: InMemoryBlobStore,
    redactor: Optional[Callable[[Any], Any]] = None,
) -> None:
    configure(
        WorkerContext(
            mcp_call=_mcp_ok,
            llm=_llm_ok,
            blob_store=blobs,
            trajectory_sink=sink,
            trajectory_blob_store=blobs,
            redactor=redactor,
        )
    )


def _step_by_cid(sink: InMemoryTrajectoryStore, cid: str) -> TrajectoryStep:
    matches = [step for step in sink.list_trajectory_steps(ROOT) if step.cid == cid]
    assert len(matches) == 1
    return matches[0]


def _stored(blobs: InMemoryBlobStore, ref: str) -> Any:
    return json.loads(asyncio.run(blobs.get(ROOT, ref)))


def test_redact_secret_shaped_recurses_preserves_non_secret_and_does_not_mutate():
    value = {
        "api_key": "x",
        "q": "hi",
        "outer": {"password": "p", "ok": 1},
        "arr": [{"token": "t"}],
        "authorization": "Bearer a",
        "bearer": "b",
        "cache_key": "cache",
        "primary_key": "primary",
        "secret": "s",
        "credential": "c",
        "private_key": "pk",
        "apikey": "ak",
    }
    original = json.loads(json.dumps(value, sort_keys=True))

    redacted = redact_secret_shaped(value)

    assert redacted == {
        "api_key": REDACTED_PLACEHOLDER,
        "q": "hi",
        "outer": {"password": REDACTED_PLACEHOLDER, "ok": 1},
        "arr": [{"token": REDACTED_PLACEHOLDER}],
        "authorization": REDACTED_PLACEHOLDER,
        "bearer": REDACTED_PLACEHOLDER,
        "cache_key": "cache",
        "primary_key": "primary",
        "secret": REDACTED_PLACEHOLDER,
        "credential": REDACTED_PLACEHOLDER,
        "private_key": REDACTED_PLACEHOLDER,
        "apikey": REDACTED_PLACEHOLDER,
    }
    assert value == original

    non_secret = {"q": "hi", "nested": [{"count": 1, "enabled": True}], "none": None}
    assert json.dumps(redact_secret_shaped(non_secret), sort_keys=True) == json.dumps(
        non_secret, sort_keys=True
    )


def test_effect_capture_redacts_secret_input_by_default():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_capture(sink=sink, blobs=blobs)
    secret_value = {"api_key": "sk-live", "q": "hi"}

    result = asyncio.run(callTool(_tool_input(secret_value)))

    assert result == {"ok": True, "seen": "hi"}
    assert secret_value == {"api_key": "sk-live", "q": "hi"}
    step = _step_by_cid(sink, "call-redact")
    assert step.input_ref is not None
    assert _stored(blobs, step.input_ref) == {
        "api_key": REDACTED_PLACEHOLDER,
        "q": "hi",
    }


def test_trajectory_recorder_redacts_input_and_output_by_default():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    recorder = TrajectoryRecorder(sink=sink, blob_store=blobs)

    step = asyncio.run(
        recorder.capture(
            step_id="local-step-1",
            run_id=RUN,
            root_run_id=ROOT,
            cid="local-cid",
            node_id="local-node",
            op="call",
            kind="tool",
            input_value={"password": "p", "q": "hi"},
            output_value={"token": "t", "hits": 1},
            causes=("up-local",),
        )
    )

    assert step.input_ref is not None
    assert step.output_ref is not None
    assert _stored(blobs, step.input_ref) == {
        "password": REDACTED_PLACEHOLDER,
        "q": "hi",
    }
    assert _stored(blobs, step.output_ref) == {
        "token": REDACTED_PLACEHOLDER,
        "hits": 1,
    }


def test_marker_capture_redacts_secret_value_by_default():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_capture(sink=sink, blobs=blobs)

    asyncio.run(
        record_marker_step(
            kind="root",
            run_id=RUN,
            root_run_id=ROOT,
            segment_seq=0,
            value={"authorization": "Bearer z", "x": 1},
            cid="root-marker",
            value_kind="input",
        )
    )

    step = _step_by_cid(sink, "root-marker")
    assert step.input_ref is not None
    assert _stored(blobs, step.input_ref) == {
        "authorization": REDACTED_PLACEHOLDER,
        "x": 1,
    }


def test_custom_redactor_replaces_default_for_worker_context_and_recorder():
    def custom(value: Any) -> Any:
        if isinstance(value, dict):
            out = dict(value)
            if isinstance(out.get("name"), str):
                out["name"] = out["name"].upper()
            return out
        return value

    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_capture(sink=sink, blobs=blobs, redactor=custom)
    asyncio.run(callTool(_tool_input({"api_key": "raw", "name": "alice"})))

    effect_step = _step_by_cid(sink, "call-redact")
    assert effect_step.input_ref is not None
    assert _stored(blobs, effect_step.input_ref) == {"api_key": "raw", "name": "ALICE"}

    local_sink = InMemoryTrajectoryStore()
    local_blobs = InMemoryBlobStore()
    recorder = TrajectoryRecorder(
        sink=local_sink,
        blob_store=local_blobs,
        redactor=custom,
    )
    local_step = asyncio.run(
        recorder.capture(
            step_id="local-custom",
            run_id=RUN,
            root_run_id=ROOT,
            cid="local-custom",
            node_id="local-node",
            op="call",
            kind="tool",
            input_value={"api_key": "raw", "name": "bob"},
            output_value={"api_key": "raw-out", "name": "carol"},
        )
    )

    assert local_step.input_ref is not None
    assert local_step.output_ref is not None
    assert _stored(local_blobs, local_step.input_ref) == {"api_key": "raw", "name": "BOB"}
    assert _stored(local_blobs, local_step.output_ref) == {
        "api_key": "raw-out",
        "name": "CAROL",
    }


def _hash_pointer(text: str) -> str:
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    return f"redacted:sha256:{digest}"


def _memmcp_redactor(value: Any) -> Any:
    pii_keys = {"content", "background", "body", "note"}
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, child in value.items():
            if isinstance(key, str) and key in pii_keys and isinstance(child, str):
                out[key] = _hash_pointer(child)
            else:
                out[key] = _memmcp_redactor(child)
        return out
    if isinstance(value, list):
        return [_memmcp_redactor(child) for child in value]
    return value


def test_memmcp_value_level_redactor_masks_free_text_payloads():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_capture(sink=sink, blobs=blobs, redactor=_memmcp_redactor)
    memory = {"kind": "memory", "content": "my SSN is 123-45-6789", "tags": ["x"]}
    checkin = {"type": "checkin", "note": "felt anxious about money", "score": 3}
    brief = {"brief_id": "b1", "body": "long free text with a name"}

    asyncio.run(callTool(_tool_input(memory, cid="memory-cid")))
    asyncio.run(callTool(_tool_input(checkin, cid="checkin-cid")))
    asyncio.run(invokeReasoner(_reasoner_input(brief, cid="brief-cid")))

    memory_step = _step_by_cid(sink, "memory-cid")
    checkin_step = _step_by_cid(sink, "checkin-cid")
    brief_step = _step_by_cid(sink, "brief-cid")
    assert memory_step.input_ref is not None
    assert checkin_step.input_ref is not None
    assert brief_step.input_ref is not None
    assert _stored(blobs, memory_step.input_ref) == {
        "kind": "memory",
        "content": _hash_pointer("my SSN is 123-45-6789"),
        "tags": ["x"],
    }
    assert _stored(blobs, checkin_step.input_ref) == {
        "type": "checkin",
        "note": _hash_pointer("felt anxious about money"),
        "score": 3,
    }
    assert _stored(blobs, brief_step.input_ref) == {
        "brief_id": "b1",
        "body": _hash_pointer("long free text with a name"),
    }


def test_export_hydrated_redacts_raw_secret_blob_by_default():
    async def scenario() -> None:
        blobs = InMemoryBlobStore()
        raw = {"api_key": "raw-secret", "q": "hi"}
        ref = await blobs.put(ROOT, _canonical(raw))
        store = InMemoryTrajectoryStore()
        store.start_run(TrajectoryRun(run_id=RUN, root_run_id=ROOT))
        store.append_steps([
            TrajectoryStep(
                step_id="step-1",
                run_id=RUN,
                root_run_id=ROOT,
                cid="cid-1",
                node_id="node-1",
                op="call",
                kind="tool",
                input_ref=ref,
                output_ref=ref,
            )
        ])
        store.record_values([
            TrajectoryValue(ref=ref, root_run_id=ROOT, step_id="step-1", kind="input")
        ])

        lines = await store.export_trajectory_jsonl_hydrated(ROOT, blobs)

        exported = json.loads(lines[0])
        expected = {"api_key": REDACTED_PLACEHOLDER, "q": "hi"}
        assert exported["input"] == expected
        assert exported["output"] == expected

    asyncio.run(scenario())


def test_export_hydrated_allow_raw_warns_and_returns_unredacted(caplog: pytest.LogCaptureFixture):
    async def scenario() -> None:
        blobs = InMemoryBlobStore()
        raw = {"api_key": "raw-secret", "q": "hi"}
        ref = await blobs.put(ROOT, _canonical(raw))
        store = InMemoryTrajectoryStore()
        store.start_run(TrajectoryRun(run_id=RUN, root_run_id=ROOT))
        store.append_steps([
            TrajectoryStep(
                step_id="step-raw",
                run_id=RUN,
                root_run_id=ROOT,
                cid="cid-raw",
                node_id="node-raw",
                op="call",
                kind="tool",
                input_ref=ref,
            )
        ])

        caplog.set_level(logging.WARNING, logger="julep.trajectory")
        lines = await store.export_trajectory_jsonl_hydrated(
            ROOT,
            blobs,
            allow_raw=True,
        )

        assert json.loads(lines[0])["input"] == raw
        assert any(
            "export_trajectory_jsonl_hydrated allow_raw=True" in record.message
            for record in caplog.records
        )

    asyncio.run(scenario())


class _CountingBlobStore(InMemoryBlobStore):
    def __init__(self) -> None:
        super().__init__()
        self.puts: list[bytes] = []

    async def put(self, tenant: str, data: bytes) -> str:
        self.puts.append(data)
        return await super().put(tenant, data)


def test_raising_redactor_drops_values_and_persists_nothing_raw():
    def raising(value: Any) -> Any:
        raise RuntimeError("boom")

    sink = InMemoryTrajectoryStore()
    blobs = _CountingBlobStore()
    _configure_capture(sink=sink, blobs=blobs, redactor=raising)
    before = trajectory_best_effort_failures()

    result = asyncio.run(callTool(_tool_input({"api_key": "sk-live", "q": "hi"})))

    assert result == {"ok": True, "seen": "hi"}
    step = _step_by_cid(sink, "call-redact")
    assert step.input_ref is None
    assert step.output_ref is None
    assert blobs.puts == []
    assert trajectory_best_effort_failures() >= before + 2


def test_non_secret_capture_stores_byte_identical_canonical_json():
    sink = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    _configure_capture(sink=sink, blobs=blobs)
    payload = {"q": "hi", "filters": [{"field": "title", "value": "needle"}]}

    asyncio.run(callTool(_tool_input(payload)))

    step = _step_by_cid(sink, "call-redact")
    assert step.input_ref is not None
    assert asyncio.run(blobs.get(ROOT, step.input_ref)) == _canonical(payload)
