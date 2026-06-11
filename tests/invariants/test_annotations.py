from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

pytest.importorskip("temporalio")

from composable_agents import Ann, CacheHint, call, freeze, mcp, think
from composable_agents.execution import harness
from composable_agents.execution.interpreter import interpret
from composable_agents.execution.timeouts import activity_timeout
from composable_agents.projection import InMemoryProjection, ProjectionEmitter
from conftest import read_snapshot, run


def test_activity_timeout_prefers_node_timeout_when_set() -> None:
    assert activity_timeout(7, 30) == timedelta(seconds=7)


def test_activity_timeout_uses_default_when_node_timeout_absent() -> None:
    assert activity_timeout(None, 30) == timedelta(seconds=30)


def test_call_and_think_nodes_resolve_annotation_timeout_with_helper() -> None:
    call_node = call(mcp("srv", "search"), ann=Ann(timeout_s=9))
    think_node = think("summarizer", ann=Ann(timeout_s=17))

    assert call_node.ann is not None
    assert think_node.ann is not None
    assert activity_timeout(call_node.ann.timeout, 30) == timedelta(seconds=9)
    assert activity_timeout(think_node.ann.timeout, 120) == timedelta(seconds=17)


def _temporal_env(manifest, policy: harness.ExecutionPolicy) -> harness._TemporalEnv:
    async def gate_waiter(value: Any, cid: str, timeout_s: int | None) -> Any:
        return {"value": value, "cid": cid, "timeout_s": timeout_s}

    return harness._TemporalEnv(
        manifest,
        ProjectionEmitter(InMemoryProjection()),
        session_id="annotation-test",
        manifest_json=None,
        policy=policy,
        gate_waiter=gate_waiter,
    )


def test_interpreter_forwards_call_timeout_and_cache_to_temporal_activity(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_execute_activity(activity, arg, **kwargs):
        captured["activity"] = activity
        captured["arg"] = arg
        captured["timeout"] = kwargs["start_to_close_timeout"]
        return {"ok": True}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    flow = call(
        mcp("srv", "search"),
        ann=Ann(timeout_s=5, cache=CacheHint(key="search:{q}", ttl_s=60)),
    )
    fr = freeze(flow, read_snapshot("search"))
    env = _temporal_env(fr.manifest, harness.ExecutionPolicy(hand_timeout_s=30))

    out = run(interpret(fr.flow, {"q": "x"}, env))

    assert out.value == {"ok": True}
    assert captured["activity"] is harness.callHand
    assert captured["timeout"] == timedelta(seconds=5)
    assert captured["arg"].cache == {"key": "search:{q}", "ttlS": 60}


def test_interpreter_forwards_call_retry_ann_to_temporal_activity(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_execute_activity(activity, arg, **kwargs):
        captured["retry_policy"] = kwargs["retry_policy"]
        return {"ok": True}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    flow = call(
        mcp("srv", "search"),
        ann=Ann(max_attempts=4, retry_interval_s=0.25, backoff_rate=1.5),
    )
    fr = freeze(flow, read_snapshot("search"))
    env = _temporal_env(fr.manifest, harness.ExecutionPolicy())

    out = run(interpret(fr.flow, {"q": "x"}, env))

    retry_policy = captured["retry_policy"]
    assert out.value == {"ok": True}
    assert retry_policy.maximum_attempts == 4
    assert retry_policy.initial_interval == timedelta(seconds=0.25)
    assert retry_policy.backoff_coefficient == 1.5


def test_interpreter_forwards_think_timeout_to_temporal_activity(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_execute_activity(activity, arg, **kwargs):
        captured["activity"] = activity
        captured["arg"] = arg
        captured["timeout"] = kwargs["start_to_close_timeout"]
        return {"summary": arg.value}

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    fr = freeze(think("summarizer", ann=Ann(timeout_s=13)), read_snapshot())
    env = _temporal_env(fr.manifest, harness.ExecutionPolicy(brain_timeout_s=120))

    out = run(interpret(fr.flow, {"doc": "x"}, env))

    assert out.value == {"summary": {"doc": "x"}}
    assert captured["activity"] is harness.invokeBrain
    assert captured["arg"].brain == "summarizer"
    assert captured["timeout"] == timedelta(seconds=13)
