from __future__ import annotations

import asyncio
import logging
from typing import Any

from julep.agent_loop import (
    STATE_SCHEMA_VERSION,
    AgentConfig,
    AgentState,
    TraceEntry,
    drive_agent_loop,
)


def test_sync_tool_error_becomes_observation_and_warning(caplog) -> None:
    tool = "calc/fail"
    exc = RuntimeError("sync boom")
    expected_error = repr(exc)
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {"tool": tool, "input": {"n": 1}}
        assert payload["input"] == {"error": expected_error, "tool": tool}
        return {"output": {"handled": payload["input"]}}

    def call_tool(actual_tool: str, value: Any) -> Any:
        assert actual_tool == tool
        assert value == {"n": 1}
        raise exc

    with caplog.at_level(logging.WARNING, logger="julep.turn"):
        out = asyncio.run(
            drive_agent_loop(
                input={"task": "go"},
                cfg=AgentConfig(),
                invoke_controller=invoke_controller,
                call_tool=call_tool,
            )
        )

    assert out["status"] == "done"
    assert out["output"] == {"handled": {"error": expected_error, "tool": tool}}
    assert out["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": tool, "error": expected_error}
    ]
    assert seen_payloads[1]["input"] == {"error": expected_error, "tool": tool}
    assert seen_payloads[1]["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": tool, "error": expected_error}
    ]
    assert any(
        record.name == "julep.turn" and record.levelno == logging.WARNING
        for record in caplog.records
    )


def test_async_tool_error_becomes_observation() -> None:
    tool = "calc/async-fail"
    exc = ValueError("async boom")
    expected_error = repr(exc)
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {"tool": tool, "input": 2}
        assert payload["input"] == {"error": expected_error, "tool": tool}
        return {"output": "handled async error"}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        assert (actual_tool, value) == (tool, 2)
        raise exc

    out = asyncio.run(
        drive_agent_loop(
            input=1,
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "done"
    assert out["output"] == "handled async error"
    assert out["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": tool, "error": expected_error}
    ]
    assert seen_payloads[1]["input"] == {"error": expected_error, "tool": tool}


def test_subflow_error_becomes_observation() -> None:
    ref = "child/flow"
    exc = LookupError("child exploded")
    expected_error = repr(exc)
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {"sub": ref, "input": {"item": 3}, "shape": "Pipeline"}
        assert payload["input"] == {"error": expected_error, "tool": ref}
        return {"output": {"subflow_error": payload["input"]}}

    async def call_tool(tool: str, value: Any) -> Any:
        raise AssertionError("tool runner must not be used for subflow decisions")

    async def run_subflow(actual_ref: str, value: Any) -> Any:
        assert actual_ref == ref
        assert value == {"item": 3}
        raise exc

    out = asyncio.run(
        drive_agent_loop(
            input={"task": "sub"},
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            run_subflow=run_subflow,
            granted_subflows={ref},
        )
    )

    assert out["status"] == "done"
    assert out["output"] == {"subflow_error": {"error": expected_error, "tool": ref}}
    assert out["trace"] == [
        {
            "decision": "sub",
            "cost": 5.0,
            "ref": ref,
            "shape": "Pipeline",
            "error": expected_error,
        }
    ]
    assert seen_payloads[1]["input"] == {"error": expected_error, "tool": ref}


def test_trace_entry_error_serialization_omits_when_unset_and_round_trips_when_set() -> None:
    without_error = TraceEntry(decision="call", ref="search", cost=1.0)
    assert "error" not in without_error.to_json()

    expected_error = "RuntimeError('boom')"
    with_error = TraceEntry(
        decision="call",
        ref="search",
        cost=1.0,
        error=expected_error,
    )

    encoded = with_error.to_json()
    assert encoded == {
        "decision": "call",
        "cost": 1.0,
        "ref": "search",
        "error": expected_error,
    }
    restored = TraceEntry.from_json(encoded)
    assert restored.error == expected_error
    assert restored.to_json() == encoded


def test_old_format_trace_json_and_agent_state_still_load() -> None:
    assert STATE_SCHEMA_VERSION == 1

    old_trace = {"decision": "call", "cost": 1.0, "ref": "search"}
    restored_trace = TraceEntry.from_json(old_trace)
    assert restored_trace.error is None
    assert restored_trace.to_json() == old_trace

    old_state = {
        "schemaVersion": 1,
        "round": 1,
        "cost": 3.0,
        "last": {"ok": True},
        "trace": [
            old_trace,
            {"decision": "sub", "cost": 5.0, "ref": "child", "shape": "Pipeline"},
        ],
    }
    restored_state = AgentState.from_json(old_state)
    assert [entry.error for entry in restored_state.trace] == [None, None]
    assert restored_state.to_json() == old_state


def test_denial_still_halts_without_invoking_tool() -> None:
    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return {"tool": "net/fetch", "input": "https://example.com"}

    async def call_tool(tool: str, value: Any) -> Any:
        raise AssertionError("denied tool must not run")

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            granted={"calc/add"},
        )
    )

    assert out["status"] == "denied"
    assert "not granted" in out["reason"]
    assert out["trace"] == []


def test_retry_after_tool_error_can_succeed() -> None:
    tool = "calc/flaky"
    exc = RuntimeError("first attempt failed")
    expected_error = repr(exc)
    seen_payloads: list[dict[str, Any]] = []
    call_count = 0

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {"tool": tool, "input": 10}
        if payload["input"] == {"error": expected_error, "tool": tool}:
            return {"tool": tool, "input": 10}
        return {"output": {"final": payload["input"]}}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        nonlocal call_count
        assert actual_tool == tool
        assert value == 10
        call_count += 1
        if call_count == 1:
            raise exc
        return {"ok": True, "attempt": call_count}

    out = asyncio.run(
        drive_agent_loop(
            input=0,
            cfg=AgentConfig(),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "done"
    assert out["output"] == {"final": {"ok": True, "attempt": 2}}
    assert out["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": tool, "error": expected_error},
        {"decision": "call", "cost": 1.0, "ref": tool},
    ]
    assert seen_payloads[1]["input"] == {"error": expected_error, "tool": tool}
    assert seen_payloads[2]["input"] == {"ok": True, "attempt": 2}


def test_throwing_tool_still_counts_against_max_calls() -> None:
    tool = "calc/limited"
    exc = RuntimeError("always fails")
    expected_error = repr(exc)
    seen_payloads: list[dict[str, Any]] = []
    call_count = 0

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        return {"tool": tool, "input": payload["input"]}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        nonlocal call_count
        assert actual_tool == tool
        call_count += 1
        raise exc

    out = asyncio.run(
        drive_agent_loop(
            input=0,
            cfg=AgentConfig(max_rounds=3),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            contracts={tool: {"maxCalls": 1}},
        )
    )

    assert out["status"] == "denied"
    assert out["output"] == {"error": expected_error, "tool": tool}
    assert out["callCounts"] == {tool: 1}
    assert out["trace"] == [
        {"decision": "call", "cost": 1.0, "ref": tool, "error": expected_error}
    ]
    assert call_count == 1
    assert seen_payloads[1]["input"] == {"error": expected_error, "tool": tool}
