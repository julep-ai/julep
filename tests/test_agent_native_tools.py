from __future__ import annotations

import asyncio
from typing import Any

from julep import Agent
from julep import app, arr, recv, register_pure, scan, seq
from julep import tool
from julep.agent_loop import (
    DEFAULT_THINK_COST,
    DEFAULT_TOOL_COST,
    AgentConfig,
    Decision,
    NATIVE_TOOLS_KEY,
    RoundAction,
    TraceEntry,
    action_cost,
    drive_agent_loop,
    interpret_reasoner_reply,
)
from julep.execution.interpreter import _app_config
from julep.ir import Node


def test_interpret_reasoner_reply_native_tool_calls() -> None:
    reply = {
        "tool_calls": [
            {"id": "call-1", "tool": "search", "input": {"q": "x"}},
            {"id": "call-2", "tool": "fetch", "input": {"url": "https://example.com"}},
        ]
    }

    action = interpret_reasoner_reply(reply, strict=True, native_tools=True)

    assert action.decision is Decision.CALL_MANY
    assert action.payload == [
        {"id": "call-1", "tool": "search", "input": {"q": "x"}},
        {"id": "call-2", "tool": "fetch", "input": {"url": "https://example.com"}},
    ]

    single = interpret_reasoner_reply(
        {"tool_calls": [{"id": "call-1", "tool": "search", "input": {"q": "x"}}]},
        strict=True,
        native_tools=True,
    )
    assert single.decision is Decision.CALL_MANY
    assert single.payload == [
        {"id": "call-1", "tool": "search", "input": {"q": "x"}},
    ]

    missing_tool = interpret_reasoner_reply(
        {"tool_calls": [{"id": "call-1", "input": {"q": "x"}}]},
        strict=True,
        native_tools=True,
    )
    assert missing_tool.decision is Decision.CONTROLLER_ERROR

    non_dict = interpret_reasoner_reply(
        {"tool_calls": ["not a call"]},
        strict=True,
        native_tools=True,
    )
    assert non_dict.decision is Decision.CONTROLLER_ERROR

    default_parser = interpret_reasoner_reply(reply, strict=True)
    assert default_parser.decision is Decision.CONTROLLER_ERROR


def test_native_tools_plain_final_values_finish() -> None:
    """Provider-native rounds distinguish calls via tool_calls, not value shape."""

    for reply in ("plain final answer", ["one", "two"], 7):
        action = interpret_reasoner_reply(reply, strict=True, native_tools=True)
        assert action.decision is Decision.FINISH
        assert action.payload == reply

        legacy = interpret_reasoner_reply(reply, strict=True, native_tools=False)
        assert legacy.decision is Decision.CONTROLLER_ERROR


def test_native_tools_malformed_reserved_action_does_not_finish() -> None:
    for reply in (
        {"done": False, "answer": "not actually done"},
        {"done": False, "output": "contradictory"},
        {"tool_calls": [{"tool": "", "input": {}}]},
    ):
        action = interpret_reasoner_reply(
            reply,
            strict=True,
            native_tools=True,
        )
        assert action.decision is Decision.CONTROLLER_ERROR


def test_native_tools_rejects_contradictory_action_families() -> None:
    for reply in (
        {"done": True, "tool": "search"},
        {"tool_calls": [{"tool": "search", "input": {}}], "done": True},
        {"output": "answer", "escalate": "human"},
        {"tool": "search", "sub": "child"},
        {"tool_calls": [{"tool": "search", "input": {}}], "tool": "search"},
    ):
        for strict in (True, False):
            action = interpret_reasoner_reply(
                reply,
                strict=strict,
                native_tools=True,
            )
            assert action.decision is Decision.CONTROLLER_ERROR


def test_native_tools_accepts_done_with_output_as_one_finish_action() -> None:
    action = interpret_reasoner_reply(
        {"done": True, "output": {"answer": 42}},
        strict=True,
        native_tools=True,
    )

    assert action.decision is Decision.FINISH
    assert action.payload == {"answer": 42}


def test_action_cost_for_call_many_charges_each_call() -> None:
    action = RoundAction(
        Decision.CALL_MANY,
        [
            {"id": "call-1", "tool": "one", "input": 1},
            {"id": "call-2", "tool": "two", "input": 2},
            {"id": "call-3", "tool": "three", "input": 3},
        ],
    )

    assert action_cost(action) == 3 * DEFAULT_TOOL_COST


def test_agent_config_native_tools_json_round_trips() -> None:
    plain = AgentConfig()
    plain_json = plain.to_json()
    assert "nativeTools" not in plain_json

    restored_plain = AgentConfig.from_json(plain_json)
    assert restored_plain.native_tools is False
    assert restored_plain.to_json() == plain_json

    native = AgentConfig(native_tools=True)
    native_json = native.to_json()
    assert native_json["nativeTools"] is True

    restored_native = AgentConfig.from_json(native_json)
    assert restored_native.native_tools is True
    assert restored_native.to_json() == native_json

    assert AgentConfig.from_json({"native_tools": True}).native_tools is True
    assert AgentConfig.from_json({}).native_tools is False


def test_app_ir_serializes_native_tool_flags_and_round_trips() -> None:
    encoded = app(
        "c",
        tools=["x"],
        native_tools=True,
        require_tool_call=True,
    ).to_json()

    assert encoded["nativeTools"] is True
    assert encoded["requireToolCall"] is True
    assert Node.from_json(encoded).to_json() == encoded


def test_app_ir_omits_native_tool_flags_when_false() -> None:
    encoded = app("c", tools=["x"]).to_json()

    assert "nativeTools" not in encoded
    assert "requireToolCall" not in encoded


def test_native_tools_reply_schema_rejects_reserved_action_keys() -> None:
    from julep.validate import blocking, validate

    reserved = app(
        "c",
        tools=["x"],
        native_tools=True,
        output_schema={
            "type": "object",
            "properties": {"tool": {"type": "string"}},
        },
    )
    assert {diag.code for diag in blocking(validate(reserved))} >= {"APP_RESERVED_REPLY_KEY"}

    ordinary = app(
        "c",
        tools=["x"],
        native_tools=True,
        output_schema={
            "type": "object",
            "properties": {"action": {"type": "string"}},
        },
    )
    assert "APP_RESERVED_REPLY_KEY" not in {diag.code for diag in blocking(validate(ordinary))}


def test_native_tools_reply_schema_finds_composed_top_level_reserved_keys() -> None:
    from julep.validate import blocking, validate

    reserved_property = {
        "type": "object",
        "properties": {"tool": {"type": "string"}},
    }
    composed_schemas = (
        {"oneOf": [reserved_property]},
        {"anyOf": [reserved_property]},
        {"allOf": [reserved_property]},
        {"if": reserved_property},
        {"then": reserved_property},
        {"else": reserved_property},
        {"dependentSchemas": {"kind": reserved_property}},
        {
            "$ref": "#/$defs/result",
            "$defs": {"result": reserved_property},
        },
        {
            "$ref": "#/$defs/loop",
            "$defs": {
                "loop": {
                    "allOf": [
                        {"$ref": "#/$defs/loop"},
                        reserved_property,
                    ]
                }
            },
        },
    )

    for output_schema in composed_schemas:
        flow = app(
            "c",
            tools=["x"],
            native_tools=True,
            output_schema=output_schema,
        )
        assert "APP_RESERVED_REPLY_KEY" in {diag.code for diag in blocking(validate(flow))}


def test_native_tools_reply_schema_ignores_nested_property_value_schemas() -> None:
    from julep.validate import blocking, validate

    flow = app(
        "c",
        tools=["x"],
        native_tools=True,
        output_schema={
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "properties": {"tool": {"type": "string"}},
                }
            },
            "$defs": {
                "unused": {
                    "type": "object",
                    "properties": {"done": {"type": "boolean"}},
                }
            },
        },
    )

    assert "APP_RESERVED_REPLY_KEY" not in {diag.code for diag in blocking(validate(flow))}


def test_app_config_surfaces_native_tool_flags_only_when_present() -> None:
    native_config = _app_config(
        app(
            "c",
            tools=["x"],
            native_tools=True,
            require_tool_call=True,
        )
    )
    assert native_config is not None
    assert native_config["nativeTools"] is True
    assert native_config["requireToolCall"] is True

    plain_config = _app_config(app("c", tools=["x"]))
    assert plain_config is not None
    assert "nativeTools" not in plain_config
    assert "requireToolCall" not in plain_config


def test_agent_facade_serializes_native_tool_flags_only_when_enabled() -> None:
    @tool(effect="read", idempotent=True, name="ir_flags_lookup")
    def lookup(value: str) -> dict[str, str]:
        return {"value": value}

    native_agent = Agent(
        "m",
        tools=[lookup],
        name="ir_flags_agent",
        native_tools=True,
        require_tool_call=True,
    )
    native_json = native_agent.to_ir().to_json()
    assert native_json["nativeTools"] is True
    assert native_json["requireToolCall"] is True

    plain_agent = Agent("m", tools=[lookup], name="ir_no_flags_agent")
    plain_json = plain_agent.to_ir().to_json()
    assert "nativeTools" not in plain_json
    assert "requireToolCall" not in plain_json


def test_trace_entry_call_id_json_round_trips_and_loads_old_format() -> None:
    without_call_id = TraceEntry(decision="call", ref="search", cost=DEFAULT_TOOL_COST)
    assert "callId" not in without_call_id.to_json()

    with_call_id = TraceEntry(
        decision="call",
        ref="search",
        cost=DEFAULT_TOOL_COST,
        call_id="call-1",
    )
    encoded = with_call_id.to_json()
    assert encoded == {
        "decision": "call",
        "cost": DEFAULT_TOOL_COST,
        "ref": "search",
        "callId": "call-1",
    }

    restored = TraceEntry.from_json(encoded)
    assert restored.call_id == "call-1"
    assert restored.to_json() == encoded

    old_format = {"decision": "call", "cost": DEFAULT_TOOL_COST, "ref": "search"}
    restored_old = TraceEntry.from_json(old_format)
    assert restored_old.call_id is None
    assert restored_old.to_json() == old_format


def _native_tools_session_result(value: dict[str, Any]) -> tuple[None, dict[str, Any]]:
    return None, value


register_pure(
    "tests.agent_native_tools.session_result",
    _native_tools_session_result,
)


def test_call_many_executes_two_tools_and_threads_ordered_observations() -> None:
    seen_payloads: list[dict[str, Any]] = []
    calls: list[tuple[str, Any, int | None]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {
                "tool_calls": [
                    {"id": "call-1", "tool": "left", "input": {"n": 1}},
                    {"id": "call-2", "tool": "right", "input": {"n": 2}},
                ]
            }
        assert payload["input"] == [
            {"id": "call-1", "tool": "left", "output": {"tool": "left", "n": 1}},
            {"id": "call-2", "tool": "right", "output": {"tool": "right", "n": 2}},
        ]
        return {"done": True, "output": {"seen": payload["input"]}}

    async def call_tool(
        actual_tool: str,
        value: Any,
        *,
        call_index: int | None = None,
    ) -> Any:
        calls.append((actual_tool, value, call_index))
        return {"tool": actual_tool, "n": value["n"]}

    out = asyncio.run(
        drive_agent_loop(
            input={"task": "go"},
            cfg=AgentConfig(native_tools=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    expected_last = [
        {"id": "call-1", "tool": "left", "output": {"tool": "left", "n": 1}},
        {"id": "call-2", "tool": "right", "output": {"tool": "right", "n": 2}},
    ]
    assert out["status"] == "done"
    assert out["rounds"] == 1
    assert out["cost"] == (2 * DEFAULT_THINK_COST) + (2 * DEFAULT_TOOL_COST)
    assert out["output"] == {"seen": expected_last}
    assert calls == [("left", {"n": 1}, 0), ("right", {"n": 2}, 1)]
    assert seen_payloads[1]["input"] == expected_last
    assert out["trace"] == [
        {
            "decision": "call",
            "cost": DEFAULT_TOOL_COST,
            "ref": "left",
            "callId": "call-1",
            "arguments": {"n": 1},
        },
        {
            "decision": "call",
            "cost": DEFAULT_TOOL_COST,
            "ref": "right",
            "callId": "call-2",
            "arguments": {"n": 2},
        },
    ]


def test_call_many_read_tools_run_concurrently() -> None:
    events: list[str] = []
    started: set[str] = set()
    both_started = asyncio.Event()

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        if not events:
            return {
                "tool_calls": [
                    {"id": "call-1", "tool": "read-a", "input": "a"},
                    {"id": "call-2", "tool": "read-b", "input": "b"},
                ]
            }
        return {"done": True, "output": payload["input"]}

    async def call_tool(
        actual_tool: str,
        value: Any,
        *,
        call_index: int | None = None,
    ) -> Any:
        del call_index
        events.append(f"{actual_tool}:started")
        started.add(actual_tool)
        if started == {"read-a", "read-b"}:
            both_started.set()
        await asyncio.wait_for(both_started.wait(), timeout=0.25)
        await asyncio.sleep(0)
        events.append(f"{actual_tool}:finished")
        return value

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(native_tools=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            contracts={
                "read-a": {"effect": "read"},
                "read-b": {"effect": "read"},
            },
        )
    )

    first_finish = min(index for index, event in enumerate(events) if event.endswith(":finished"))
    assert out["status"] == "done"
    assert events.index("read-a:started") < first_finish
    assert events.index("read-b:started") < first_finish


def test_call_many_write_starts_after_read_finishes_even_when_emitted_first() -> None:
    events: list[str] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        if not events:
            return {
                "tool_calls": [
                    {"id": "call-write", "tool": "write", "input": "w"},
                    {"id": "call-read", "tool": "read", "input": "r"},
                ]
            }
        return {"done": True, "output": payload["input"]}

    async def call_tool(
        actual_tool: str,
        value: Any,
        *,
        call_index: int | None = None,
    ) -> Any:
        del call_index
        events.append(f"{actual_tool}:started")
        if actual_tool == "read":
            await asyncio.sleep(0.01)
        events.append(f"{actual_tool}:finished")
        return value

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(native_tools=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            contracts={
                "read": {"effect": "read"},
                "write": {"effect": "write"},
            },
        )
    )

    assert out["status"] == "done"
    assert events.index("read:finished") < events.index("write:started")


def test_call_many_denial_halts_whole_round_before_any_tool_executes() -> None:
    calls: list[tuple[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        return {
            "tool_calls": [
                {"id": "call-1", "tool": "allowed", "input": 1},
                {"id": "call-2", "tool": "denied", "input": 2},
            ]
        }

    async def call_tool(
        actual_tool: str,
        value: Any,
        *,
        call_index: int | None = None,
    ) -> Any:
        del call_index
        calls.append((actual_tool, value))
        return value

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(native_tools=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
            granted={"allowed"},
        )
    )

    assert out["status"] == "denied"
    assert "not granted" in out["reason"]
    assert out["rounds"] == 0
    assert calls == []
    assert out["trace"] == []


def test_call_many_one_failing_tool_only_errors_that_observation() -> None:
    exc = RuntimeError("boom")
    expected_error = repr(exc)
    seen_payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            return {
                "tool_calls": [
                    {"id": "call-ok", "tool": "ok", "input": 1},
                    {"id": "call-fail", "tool": "fail", "input": 2},
                ]
            }
        return {"done": True, "output": {"final": payload["input"]}}

    async def call_tool(
        actual_tool: str,
        value: Any,
        *,
        call_index: int | None = None,
    ) -> Any:
        del call_index
        if actual_tool == "fail":
            raise exc
        return {"value": value}

    out = asyncio.run(
        drive_agent_loop(
            input="q",
            cfg=AgentConfig(native_tools=True),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    expected_last = [
        {"id": "call-ok", "tool": "ok", "output": {"value": 1}},
        {
            "id": "call-fail",
            "tool": "fail",
            "output": {"error": expected_error, "tool": "fail"},
        },
    ]
    assert out["status"] == "done"
    assert out["output"] == {"final": expected_last}
    assert seen_payloads[1]["input"] == expected_last
    assert out["trace"] == [
        {
            "decision": "call",
            "cost": DEFAULT_TOOL_COST,
            "ref": "ok",
            "callId": "call-ok",
            "arguments": 1,
        },
        {
            "decision": "call",
            "cost": DEFAULT_TOOL_COST,
            "ref": "fail",
            "callId": "call-fail",
            "arguments": 2,
            "error": expected_error,
        },
    ]


def test_provider_tool_defs_uses_tool_schema_and_docstring() -> None:
    from julep.agent import provider_tool_defs

    @tool(effect="read", idempotent=True)
    def lookup_weather(city: str, days: int) -> dict[str, Any]:
        """Look up weather for a city."""
        return {"city": city, "days": days}

    assert provider_tool_defs([lookup_weather]) == [
        {
            "type": "function",
            "function": {
                "name": lookup_weather.name,
                "description": "Look up weather for a city.",
                "parameters": lookup_weather.input_schema,
            },
        }
    ]


def test_agent_facade_passes_provider_tool_defs_only_when_native_tools_enabled() -> None:
    from julep.agent import provider_tool_defs

    @tool(effect="read", idempotent=True, name="native_facade_lookup")
    def lookup_weather(city: str) -> dict[str, str]:
        """Look up weather for a city."""
        return {"city": city}

    expected_defs = provider_tool_defs([lookup_weather])
    native_payloads: list[dict[str, Any]] = []

    def native_llm(_reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        native_payloads.append(payload)
        assert payload[NATIVE_TOOLS_KEY] == expected_defs
        return {"done": True, "output": "native-ok"}

    native_agent = Agent(
        "m",
        tools=[lookup_weather],
        name="agent_native_tools_facade_payload",
        native_tools=True,
        llm=native_llm,
    )
    native_result = native_agent.run("sf")

    assert native_result["status"] == "done"
    assert native_result["output"] == "native-ok"
    assert native_payloads[0][NATIVE_TOOLS_KEY] == expected_defs

    legacy_payloads: list[dict[str, Any]] = []

    def legacy_llm(_reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        legacy_payloads.append(payload)
        assert "tools" not in payload
        return {"done": True, "output": "legacy-ok"}

    legacy_agent = Agent(
        "m",
        tools=[lookup_weather],
        name="agent_native_tools_facade_legacy_payload",
        llm=legacy_llm,
    )
    legacy_result = legacy_agent.run("sf")

    assert legacy_result["status"] == "done"
    assert legacy_result["output"] == "legacy-ok"
    assert "tools" not in legacy_payloads[0]


def test_agent_open_local_session_passes_provider_tool_defs_for_native_tools() -> None:
    from julep.agent import provider_tool_defs
    from conftest import run

    @tool(effect="read", idempotent=True, name="native_session_left")
    def left(value: dict[str, int]) -> dict[str, int]:
        return {"left": value["n"]}

    @tool(effect="read", idempotent=True, name="native_session_right")
    def right(value: dict[str, int]) -> dict[str, int]:
        return {"right": value["n"]}

    expected_defs = provider_tool_defs([left, right])
    payloads: list[dict[str, Any]] = []

    def llm(_reasoner_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        payloads.append(payload)
        assert payload[NATIVE_TOOLS_KEY] == expected_defs
        if len(payloads) == 1:
            return {
                "tool_calls": [
                    {"id": "a", "tool": left.name, "input": {"n": 1}},
                    {"id": "b", "tool": right.name, "input": {"n": 2}},
                ]
            }
        return {"done": True, "output": payload["input"]}

    async def main() -> None:
        agent = Agent(
            "m",
            tools=[left, right],
            name="agent_native_tools_session",
            native_tools=True,
            llm=llm,
        )
        session = scan(
            seq(
                recv("in"),
                app("agent_native_tools_session"),
                arr("tests.agent_native_tools.session_result"),
            ),
            init=None,
            in_channel="in",
            out_channel="out",
        )
        handle = await agent.open(session=session, backend="local")
        agen = handle.events()
        await handle.send({"task": "go"})
        emitted = None
        for _ in range(100):
            event = await asyncio.wait_for(agen.__anext__(), timeout=1.0)
            if event.is_emit:
                emitted = event.payload
                break
        assert emitted is not None
        assert emitted["status"] == "done"
        assert emitted["output"] == [
            {"id": "a", "tool": left.name, "output": {"left": 1}},
            {"id": "b", "tool": right.name, "output": {"right": 2}},
        ]
        await handle.close()

    run(main())
