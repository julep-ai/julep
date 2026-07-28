"""Progressive skill disclosure: the prompt block, the tool, and the inner loop."""

from __future__ import annotations

import json
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
    reg, keys = _registry_with(ALPHA)
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

    async def acompletion(**kwargs: Any) -> Any:
        return _skill_call("alpha")

    result = run(complete_reasoner(_reasoner(keys), "hi", acompletion=acompletion))
    calls = result.reply.get("tool_calls", []) if isinstance(result.reply, dict) else []
    assert all(call["tool"] != SKILL_TOOL for call in calls)
    assert result.meta.native_tool_calls == 0


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
