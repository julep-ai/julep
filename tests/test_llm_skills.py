"""Progressive skill disclosure: the prompt block, the tool, and the inner loop."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

import pytest

from conftest import run
from julep.dotctx import Reasoner
from julep.execution.llm import complete_reasoner
from julep.registry import Registry
from julep.skills import (
    SKILL_TOOL,
    Skill,
    batch_system_text,
    inline_skills_block,
    load_skill_tool_def,
    resolve_skill_keys,
    skills_prompt_block,
)

ALPHA = Skill(name="alpha", description="Use for alpha work.", body="ALPHA BODY")
BETA = Skill(name="beta", description="Use for beta work.", body="BETA BODY")


def test_prompt_block_lists_names_and_descriptions_but_never_bodies() -> None:
    block = skills_prompt_block([ALPHA, BETA])
    assert "alpha" in block and "Use for alpha work." in block
    assert "beta" in block and "Use for beta work." in block
    assert "ALPHA BODY" not in block and "BETA BODY" not in block
    assert SKILL_TOOL in block


def test_tool_def_enumerates_only_undisclosed_skills() -> None:
    definition = load_skill_tool_def([ALPHA, BETA], loaded=["alpha"])
    assert definition["function"]["name"] == SKILL_TOOL
    enum = definition["function"]["parameters"]["properties"]["name"]["enum"]
    assert enum == ["beta"]
    assert definition["function"]["parameters"]["required"] == ["name"]


def test_inline_block_carries_full_bodies() -> None:
    block = inline_skills_block([ALPHA])
    assert "ALPHA BODY" in block and "Use for alpha work." in block


def test_resolve_skill_keys_reads_the_registry() -> None:
    reg = Registry()
    key = reg.register_skill(ALPHA)
    assert resolve_skill_keys([key], registry=reg) == (ALPHA,)


def test_batch_system_text_inlines_and_preserves_the_system() -> None:
    reg = Registry()
    key = reg.register_skill(ALPHA)
    text = batch_system_text("You draft.", [key], registry=reg)
    assert text.endswith("You draft.")
    assert "ALPHA BODY" in text


def test_batch_system_text_passes_through_without_skills() -> None:
    assert batch_system_text("You draft.", [], registry=Registry()) == "You draft."


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction


@dataclass
class FakeMessage:
    content: Optional[str] = None
    parsed: Any = None
    tool_calls: Optional[list[FakeToolCall]] = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]
    usage: Any = None
    model: str = "m"


def _text(content: str) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(content=content))])


def _skill_call(name: str, call_id: str = "c1") -> FakeCompletion:
    return FakeCompletion(
        choices=[
            FakeChoice(
                FakeMessage(
                    tool_calls=[
                        FakeToolCall(call_id, FakeFunction(SKILL_TOOL, json.dumps({"name": name})))
                    ]
                )
            )
        ]
    )


def _skill_call_with_arguments(arguments: str, call_id: str = "c1") -> FakeCompletion:
    return FakeCompletion(
        choices=[
            FakeChoice(
                FakeMessage(
                    tool_calls=[
                        FakeToolCall(call_id, FakeFunction(SKILL_TOOL, arguments))
                    ]
                )
            )
        ]
    )


def _tool_calls(*calls: FakeToolCall) -> FakeCompletion:
    return FakeCompletion(
        choices=[FakeChoice(FakeMessage(tool_calls=list(calls)))]
    )


def _registry_with(*skills: Skill) -> tuple[Registry, tuple[str, ...]]:
    reg = Registry()
    return reg, tuple(reg.register_skill(skill) for skill in skills)


def _reasoner(keys: tuple[str, ...], **kwargs: Any) -> Reasoner:
    return Reasoner(
        name="skilled",
        model="gemini:gemini-2.5-flash",   # prompt-fallback provider: one dispatch path
        system="You draft.",
        skills=list(keys),
        **kwargs,
    )


def test_descriptions_are_in_the_system_prompt_and_bodies_are_not(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return _text("done")

    run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    system = seen[0][0]["content"]
    assert "Use for alpha work." in system
    assert "ALPHA BODY" not in system
    assert system.rstrip().endswith("You draft.")


def test_skill_tool_is_offered_when_skills_are_active(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    seen: list[Any] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs.get("tools"))
        return _text("done")

    run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert [t["function"]["name"] for t in seen[0]] == [SKILL_TOOL]


def test_no_tool_and_no_block_without_skills() -> None:
    seen: list[Any] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs)
        return _text("done")

    run(complete_reasoner(_reasoner(()), "hi", acompletion=acompletion))
    assert "tools" not in seen[0]
    assert "Available skills" not in seen[0]["messages"][0]["content"]


def test_loading_a_skill_feeds_the_body_back_and_re_asks(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA, BETA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == "drafted"
    assert result.meta.skill_loads == ("alpha",)
    assert result.meta.to_attrs()["llm.skill_loads"] == ["alpha"]
    tool_turns = [m for m in seen[1] if m.get("role") == "tool"]
    assert tool_turns and tool_turns[0]["content"] == "ALPHA BODY"


def test_tool_is_withdrawn_after_the_last_skill_loads(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _text("drafted")])
    seen: list[Any] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs.get("tools"))
        return next(replies)

    run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert seen[0] is not None and seen[1] is None


def test_second_skill_stays_loadable(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA, BETA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _skill_call("beta", "c2"), _text("drafted")])

    async def acompletion(**kwargs: Any) -> Any:
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.meta.skill_loads == ("alpha", "beta")


def test_unknown_skill_name_is_answered_not_raised(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("ghost"), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == "drafted"
    assert result.meta.skill_loads == ()
    tool_turn = [m for m in seen[1] if m.get("role") == "tool"][0]
    assert "ghost" in tool_turn["content"] and "alpha" in tool_turn["content"]


def test_non_json_skill_arguments_are_answered_not_raised(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call_with_arguments('{"name": "al'), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == "drafted"
    assert result.meta.skill_loads == ()
    tool_turn = [m for m in seen[1] if m.get("role") == "tool"][0]
    assert SKILL_TOOL in tool_turn["content"]
    assert "name" in tool_turn["content"] and "string" in tool_turn["content"]
    assert "alpha" in tool_turn["content"]


def test_non_string_skill_name_is_answered_not_raised(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    arguments = json.dumps({"name": {"a": 1}})
    replies = iter([_skill_call_with_arguments(arguments), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == "drafted"
    assert result.meta.skill_loads == ()
    tool_turn = [m for m in seen[1] if m.get("role") == "tool"][0]
    assert SKILL_TOOL in tool_turn["content"]
    assert "name" in tool_turn["content"] and "string" in tool_turn["content"]
    assert "alpha" in tool_turn["content"]


def test_repeated_requests_cannot_spin_forever(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    calls = 0

    async def acompletion(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return _skill_call("ghost", f"c{calls}")

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert calls <= 4
    assert result.meta.skill_loads == ()


def test_skill_calls_never_leak_to_the_agent_loop(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter(
        [
            _skill_call("alpha"),
            _tool_calls(
                FakeToolCall("c2", FakeFunction(SKILL_TOOL, '{"name": "alpha"}')),
                FakeToolCall("r1", FakeFunction("lookup", '{"q": "x"}')),
            ),
        ]
    )

    async def acompletion(**kwargs: Any) -> Any:
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == {
        "tool_calls": [{"id": "r1", "tool": "lookup", "input": {"q": "x"}}]
    }
    assert result.meta.native_tool_calls == 1


def test_mixed_skill_and_real_tool_call_warns_and_reasks(monkeypatch, caplog) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter(
        [
            _tool_calls(
                FakeToolCall("c1", FakeFunction(SKILL_TOOL, '{"name": "alpha"}')),
                FakeToolCall("r1", FakeFunction("lookup", '{"q": "x"}')),
            ),
            _text("drafted"),
        ]
    )

    async def acompletion(**kwargs: Any) -> Any:
        return next(replies)

    with caplog.at_level(logging.WARNING, logger="julep.execution.llm"):
        result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))

    assert result.reply == "drafted"
    assert "lookup" not in str(result.reply)
    warning = caplog.text
    assert "skilled" in warning and "lookup" in warning
    assert "re-decided after skill disclosure" in warning


def test_skillless_json_tool_calls_payload_preserves_pre_feature_meta() -> None:
    payload = {"tool_calls": [{"tool": "lookup", "input": {"q": "x"}}]}

    async def acompletion(**kwargs: Any) -> Any:
        return _text(json.dumps(payload))

    result = run(
        complete_reasoner(
            _reasoner((), reply={"type": "object"}),
            "hi",
            acompletion=acompletion,
        )
    )
    assert result.reply == payload
    assert result.meta.native_tool_calls == 0


def test_skillless_json_tool_calls_payload_allows_non_dict_items() -> None:
    payload = {"tool_calls": ["oops"]}

    async def acompletion(**kwargs: Any) -> Any:
        return _text(json.dumps(payload))

    result = run(
        complete_reasoner(
            _reasoner((), reply={"type": "object"}),
            "hi",
            acompletion=acompletion,
        )
    )
    assert result.reply == payload
    assert result.meta.native_tool_calls == 0


def test_withdrawal_round_uses_plain_skill_disclosure(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    assert result.reply == "drafted"
    assert not any("tool_calls" in message for message in seen[1])
    assert not any(message.get("role") == "tool" for message in seen[1])
    assert any("ALPHA BODY" in str(message.get("content")) for message in seen[1])


def test_prompt_cache_keeps_round_note_volatile_on_disclosure(monkeypatch) -> None:
    from julep.agent_loop import ROUND_NOTE_KEY

    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _text("drafted")])
    seen: list[list[dict[str, Any]]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs["messages"])
        return next(replies)

    reasoner = Reasoner(
        name="cached-skilled",
        model="anthropic:claude-x",
        system="You draft.",
        prompt_cache="1h",
        skills=list(keys),
    )
    run(
        complete_reasoner(
            reasoner,
            {"task": "hi", ROUND_NOTE_KEY: "round note"},
            acompletion=acompletion,
        )
    )

    system = [message for message in seen[1] if message.get("role") == "system"]
    assert len(system) == 1
    blocks = system[0]["content"]
    assert blocks[-1] == {"type": "text", "text": "round note"}
    assert "round note" not in blocks[0]["text"]


def test_openai_restores_response_format_after_skill_tool_withdrawal(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _text('{"answer": "drafted"}')])
    seen: list[dict[str, Any]] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs)
        return next(replies)

    reasoner = Reasoner(
        name="openai-skilled",
        model="openai:gpt-5.5",
        system="You draft.",
        reply={"type": "object"},
        skills=list(keys),
    )
    result = run(complete_reasoner(reasoner, "hi", acompletion=acompletion))

    assert result.reply == {"answer": "drafted"}
    assert "tools" in seen[0] and "response_format" not in seen[0]
    assert "response_format" in seen[1] and "tools" not in seen[1]


def test_real_tool_name_colliding_with_the_reserved_name_is_rejected(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    tools = [{"type": "function", "function": {"name": SKILL_TOOL, "parameters": {}}}]

    async def acompletion(**kwargs: Any) -> Any:
        return _text("done")

    with pytest.raises(ValueError, match="reserved"):
        run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion, tools=tools))


def test_the_skill_tool_enum_is_never_offered_empty(monkeypatch) -> None:
    reg, keys = _registry_with(ALPHA, BETA)
    monkeypatch.setattr("julep.execution.llm.DEFAULT_REGISTRY", reg)
    replies = iter([_skill_call("alpha"), _skill_call("beta", "c2"), _text("drafted")])
    seen: list[Any] = []

    async def acompletion(**kwargs: Any) -> Any:
        seen.append(kwargs.get("tools"))
        return next(replies)

    run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))

    observed: list[Any] = []
    for payload in seen:
        if payload is None:
            observed.append(None)
            continue
        skill_tool = next(
            tool for tool in payload if tool["function"]["name"] == SKILL_TOOL
        )
        enum = skill_tool["function"]["parameters"]["properties"]["name"]["enum"]
        assert isinstance(enum, list) and enum
        observed.append(enum)
    assert observed == [["alpha", "beta"], ["beta"], None]


def test_openai_batch_inlines_skill_bodies(monkeypatch) -> None:
    from julep.execution.openai_batch import OpenAIBatchProvider

    reg, keys = _registry_with(ALPHA)
    monkeypatch.setattr("julep.execution.openai_batch.DEFAULT_REGISTRY", reg)
    reasoner = Reasoner(
        name="batched", model="openai:gpt-5.5", system="You draft.", skills=list(keys)
    )
    request = OpenAIBatchProvider().build_request("cid", reasoner, {"x": 1})
    system = request["body"]["messages"][0]["content"]
    assert "ALPHA BODY" in system and system.rstrip().endswith("You draft.")


def test_openai_batch_is_unchanged_without_skills(monkeypatch) -> None:
    from julep.execution.openai_batch import OpenAIBatchProvider

    reasoner = Reasoner(name="plain-batch", model="openai:gpt-5.5", system="You draft.")
    request = OpenAIBatchProvider().build_request("cid", reasoner, {"x": 1})
    assert request["body"]["messages"][0]["content"] == "You draft."
