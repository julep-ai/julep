from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from types import SimpleNamespace
from typing import Any

import pytest

from julep import AgentConfig, app, deploy
from julep.agent_loop import ROUND_NOTE_KEY, AgentState, drive_agent_loop
from julep.dotctx import Reasoner
from julep.execution.cma import (
    _cfg_with_app_overrides,
    _reject_round_note_on_cma,
    drive_cma_agent_loop,
)
from julep.execution.llm import complete_reasoner
from julep.ir import Node
from julep.prompt import register_renderer
from julep.registry import DEFAULT_REGISTRY, PureEntry, RendererEntry
from cma_fakes import FakeCMASession
from conftest import read_snapshot


ROUND_NOTE_NAME = "std.rounds_remaining_note"


def _replace_pure(name: str, fn: Callable[..., Any]) -> PureEntry | None:
    previous = DEFAULT_REGISTRY.pures.pop(name, None)
    DEFAULT_REGISTRY.register_pure(name, fn)
    return previous


def _restore_pure(name: str, previous: PureEntry | None) -> None:
    DEFAULT_REGISTRY.pures.pop(name, None)
    if previous is not None:
        DEFAULT_REGISTRY.pures[name] = previous


def _replace_renderer(name: str, fn: Callable[[Mapping[str, Any]], str]) -> RendererEntry | None:
    previous = DEFAULT_REGISTRY.renderers.pop(name, None)
    register_renderer(name, fn)
    return previous


def _restore_renderer(name: str, previous: RendererEntry | None) -> None:
    DEFAULT_REGISTRY.renderers.pop(name, None)
    if previous is not None:
        DEFAULT_REGISTRY.renderers[name] = previous


def _fake_completion(content: str = "ok") -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content, parsed=None),
            )
        ],
    )


def _capture_completion(captured: dict[str, Any]) -> Callable[..., Awaitable[Any]]:
    async def fake_acompletion(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return _fake_completion()

    return fake_acompletion


def test_round_note_std_pure_adds_remaining_rounds_note_each_round() -> None:
    payloads: list[dict[str, Any]] = []

    async def invoke_controller(payload: dict[str, Any]) -> Any:
        payloads.append(payload)
        if len(payloads) == 1:
            return {"tool": "lookup", "input": {"q": "julep"}}
        return {"output": "done"}

    async def call_tool(actual_tool: str, value: Any) -> Any:
        assert actual_tool == "lookup"
        assert value == {"q": "julep"}
        return {"ok": True}

    out = asyncio.run(
        drive_agent_loop(
            input={"task": "go"},
            cfg=AgentConfig(max_rounds=5, round_note=ROUND_NOTE_NAME),
            invoke_controller=invoke_controller,
            call_tool=call_tool,
        )
    )

    assert out["status"] == "done"
    assert payloads[0][ROUND_NOTE_KEY] == "[REMAINING ROUNDS: 5]"
    assert payloads[1][ROUND_NOTE_KEY] == "[REMAINING ROUNDS: 4]"


def test_complete_reasoner_appends_round_note_after_rendered_user_turn() -> None:
    renderer_name = "tests.round_note.user_render"
    note = "[REMAINING ROUNDS: 3]"

    def render_user(ctx: Mapping[str, Any]) -> str:
        return f"Rendered input: {ctx['input']}"

    previous = _replace_renderer(renderer_name, render_user)
    try:
        captured: dict[str, Any] = {}

        reasoner = Reasoner(
            name="tests.round_note.rendered_reasoner",
            model="anthropic:claude-test",
            system="system prompt",
            user_render=renderer_name,
        )
        value = {"input": "question", "trace": [], ROUND_NOTE_KEY: note}

        out = asyncio.run(
            complete_reasoner(reasoner, value, acompletion=_capture_completion(captured))
        )
    finally:
        _restore_renderer(renderer_name, previous)

    assert out.reply == "ok"
    assert captured["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "Rendered input: question"},
        {"role": "system", "content": note},
    ]


def test_complete_reasoner_hides_round_note_from_render_context() -> None:
    renderer_name = "tests.round_note.whole_context_user_render"
    note = "[REMAINING ROUNDS: 3]"

    def render_user(ctx: Mapping[str, Any]) -> str:
        return json.dumps(ctx, sort_keys=True)

    previous = _replace_renderer(renderer_name, render_user)
    try:
        captured: dict[str, Any] = {}

        reasoner = Reasoner(
            name="tests.round_note.isolated_render_context_reasoner",
            model="anthropic:claude-test",
            system="system prompt",
            user_render=renderer_name,
        )
        value = {"input": "question", "trace": [], ROUND_NOTE_KEY: note}

        out = asyncio.run(
            complete_reasoner(reasoner, value, acompletion=_capture_completion(captured))
        )
    finally:
        _restore_renderer(renderer_name, previous)

    assert out.reply == "ok"
    assert ROUND_NOTE_KEY not in captured["messages"][1]["content"]
    assert captured["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": json.dumps({"input": "question", "trace": []}, sort_keys=True)},
        {"role": "system", "content": note},
    ]


def test_complete_reasoner_appends_round_note_without_user_renderer() -> None:
    captured: dict[str, Any] = {}
    note = "[REMAINING ROUNDS: 3]"
    value = {"input": "question", "trace": [], ROUND_NOTE_KEY: note}

    reasoner = Reasoner(
        name="tests.round_note.plain_reasoner",
        model="anthropic:claude-test",
        system="system prompt",
    )

    out = asyncio.run(complete_reasoner(reasoner, value, acompletion=_capture_completion(captured)))

    assert out.reply == "ok"
    assert captured["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": json.dumps({"input": "question", "trace": []})},
        {"role": "system", "content": note},
    ]


def test_complete_reasoner_omits_trailing_round_note_when_note_absent_or_none() -> None:
    reasoner = Reasoner(
        name="tests.round_note.no_note_reasoner",
        model="anthropic:claude-test",
        system="system prompt",
    )

    for value in (
        {"input": "question", "trace": []},
        {"input": "question", "trace": [], ROUND_NOTE_KEY: None},
    ):
        captured: dict[str, Any] = {}
        expected_user = json.dumps({k: v for k, v in value.items() if k != ROUND_NOTE_KEY})

        out = asyncio.run(
            complete_reasoner(reasoner, value, acompletion=_capture_completion(captured))
        )

        assert out.reply == "ok"
        assert captured["messages"] == [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": expected_user},
        ]


def test_complete_reasoner_does_not_inject_business_note_field() -> None:
    captured: dict[str, Any] = {}
    value = {"text": "summarize", "note": "draft only"}
    reasoner = Reasoner(
        name="tests.round_note.business_note",
        model="anthropic:claude-test",
        system="system prompt",
    )
    out = asyncio.run(
        complete_reasoner(reasoner, value, acompletion=_capture_completion(captured))
    )
    assert out.reply == "ok"
    # No trailing system line; the business "note" stays intact in the user JSON.
    assert captured["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": json.dumps(value)},
    ]


def test_round_note_none_return_omits_note_key() -> None:
    name = "tests.round_note.none"

    def no_note(_ctx: dict[str, Any]) -> None:
        return None

    previous = _replace_pure(name, no_note)
    try:
        payloads: list[dict[str, Any]] = []

        async def invoke_controller(payload: dict[str, Any]) -> Any:
            payloads.append(payload)
            if len(payloads) == 1:
                return {"tool": "lookup", "input": "first"}
            return {"output": "done"}

        async def call_tool(actual_tool: str, value: Any) -> Any:
            assert (actual_tool, value) == ("lookup", "first")
            return {"ok": True}

        out = asyncio.run(
            drive_agent_loop(
                input="q",
                cfg=AgentConfig(max_rounds=3, round_note=name),
                invoke_controller=invoke_controller,
                call_tool=call_tool,
            )
        )
    finally:
        _restore_pure(name, previous)

    assert out["status"] == "done"
    assert payloads
    assert all(ROUND_NOTE_KEY not in payload for payload in payloads)


def test_round_note_non_string_return_raises_value_error() -> None:
    name = "tests.round_note.bad_type"

    def bad_note(_ctx: dict[str, Any]) -> int:
        return 12

    previous = _replace_pure(name, bad_note)
    try:
        async def invoke_controller(_payload: dict[str, Any]) -> Any:
            raise AssertionError("controller should not run")

        async def call_tool(actual_tool: str, value: Any) -> Any:
            raise AssertionError(f"tool should not run: {actual_tool} {value!r}")

        with pytest.raises(ValueError, match="round_note pure must return str"):
            asyncio.run(
                drive_agent_loop(
                    input="q",
                    cfg=AgentConfig(max_rounds=2, round_note=name),
                    invoke_controller=invoke_controller,
                    call_tool=call_tool,
                )
            )
    finally:
        _restore_pure(name, previous)


def test_round_note_ctx_contains_only_round_budget_spend_and_call_counts() -> None:
    name = "tests.round_note.capture_ctx"
    seen: list[dict[str, Any]] = []

    def capture_ctx(ctx: dict[str, Any]) -> str:
        seen.append(dict(ctx))
        return "captured"

    previous = _replace_pure(name, capture_ctx)
    try:
        payloads: list[dict[str, Any]] = []

        async def invoke_controller(payload: dict[str, Any]) -> Any:
            payloads.append(payload)
            return {"output": "done"}

        async def call_tool(actual_tool: str, value: Any) -> Any:
            raise AssertionError(f"tool should not run: {actual_tool} {value!r}")

        out = asyncio.run(
            drive_agent_loop(
                input={"ignored": True},
                cfg=AgentConfig(max_rounds=5, round_note=name),
                invoke_controller=invoke_controller,
                call_tool=call_tool,
                state=AgentState(
                    round=2,
                    spent=3.5,
                    last={"task": "go"},
                    call_counts={"lookup": 2},
                ),
            )
        )
    finally:
        _restore_pure(name, previous)

    assert out["status"] == "done"
    assert payloads[0][ROUND_NOTE_KEY] == "captured"
    assert seen == [
        {
            "round": 2,
            "maxRounds": 5,
            "spent": 3.5,
            "callCounts": {"lookup": 2},
        }
    ]
    assert set(seen[0]) == {"round", "maxRounds", "spent", "callCounts"}


def test_std_rounds_remaining_note_exact_output() -> None:
    note = DEFAULT_REGISTRY.get_pure(ROUND_NOTE_NAME)

    assert note(
        {
            "round": 4,
            "maxRounds": 9,
            "spent": 7.5,
            "callCounts": {"lookup": 2},
        }
    ) == "[REMAINING ROUNDS: 5]"


def test_agent_config_round_note_json_round_trips_and_omits_when_unset() -> None:
    plain_json = AgentConfig().to_json()
    assert "roundNote" not in plain_json

    configured = AgentConfig(round_note=ROUND_NOTE_NAME)
    configured_json = configured.to_json()
    assert configured_json["roundNote"] == ROUND_NOTE_NAME
    assert AgentConfig.from_json(configured_json).round_note == ROUND_NOTE_NAME
    assert AgentConfig.from_json({"round_note": ROUND_NOTE_NAME}).round_note == ROUND_NOTE_NAME
    assert AgentConfig.from_json({}).round_note is None


def test_app_round_note_json_round_trips_and_omits_when_unset() -> None:
    plain = app("ctl")
    assert "roundNote" not in plain.to_json()

    flow = app("ctl", round_note=ROUND_NOTE_NAME)
    encoded = flow.to_json()
    back = Node.from_json(encoded)
    snake_back = Node.from_json(
        {
            "op": "app",
            "id": "app#snake",
            "controller": "ctl",
            "round_note": ROUND_NOTE_NAME,
        }
    )

    assert encoded["roundNote"] == ROUND_NOTE_NAME
    assert back.round_note == ROUND_NOTE_NAME
    assert back.to_json() == encoded
    assert snake_back.round_note == ROUND_NOTE_NAME
    assert snake_back.to_json()["roundNote"] == ROUND_NOTE_NAME


def test_deploy_app_round_note_validates_registration_and_pins_hash() -> None:
    missing = deploy(app("ctl", round_note="not.registered"), read_snapshot(), strict=False)
    missing_unknown = [
        diag
        for diag in missing.diagnostics
        if diag.code == "UNKNOWN_PURE" and "not.registered" in diag.message
    ]

    assert missing_unknown
    assert missing.artifact_components["pureSourceHashes"] == {"not.registered": None}

    valid = deploy(app("ctl", round_note=ROUND_NOTE_NAME), read_snapshot(), strict=False)

    assert not any(diag.code == "UNKNOWN_PURE" for diag in valid.diagnostics)
    assert valid.artifact_components["pureSourceHashes"][ROUND_NOTE_NAME].startswith("pure:")


def test_cma_backend_refuses_round_note() -> None:
    async def call_tool(_tool: str, _value: Any, _cid: str) -> Any:
        raise AssertionError("must not run")

    session = FakeCMASession([])
    with pytest.raises(ValueError, match="round_note is not supported on the CMA backend"):
        asyncio.run(
            drive_cma_agent_loop(
                input="q",
                cfg=AgentConfig(max_rounds=3, round_note=ROUND_NOTE_NAME),
                session=session,
                call_tool=call_tool,
            )
        )


def test_cma_app_config_round_note_override_is_rejected() -> None:
    cfg = _cfg_with_app_overrides(
        AgentConfig(),
        {"roundNote": ROUND_NOTE_NAME},
    )

    assert cfg.round_note == ROUND_NOTE_NAME
    with pytest.raises(ValueError, match="round_note is not supported on the CMA backend"):
        _reject_round_note_on_cma(cfg)
