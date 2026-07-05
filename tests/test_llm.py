"""Tests for the any-llm-backed multi-provider LlmCaller (execution/llm.py).

No network and no any-llm install: every test injects a fake ``acompletion``
shaped like any-llm's (OpenAI-typed ``completion.choices[0].message``), so the
adapter's routing / structured-output / parsing logic is exercised in isolation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import pytest

from julep import Agent, tool
from julep.agent_loop import Decision, interpret_reasoner_reply
from julep.dotctx import Reasoner
from julep.registry import DEFAULT_REGISTRY
from julep.execution.llm import (
    _split_model,
    _strip_code_fence,
    complete_reasoner,
    make_llm_caller,
    make_local_reasoner,
)
from julep.qos import ReasonerDispatch, QoSTier
from conftest import run


# --------------------------------------------------------------------------- #
# Fakes shaped like any-llm's OpenAI-typed completion.
# --------------------------------------------------------------------------- #
@dataclass
class FakeMessage:
    content: Optional[str] = None
    parsed: Any = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]


def _completion(content: Optional[str] = None, parsed: Any = None) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(content=content, parsed=parsed))])


@dataclass
class Recorder:
    """An ``acompletion`` stand-in that records kwargs and replays a script."""

    replies: list[FakeCompletion]
    calls: list[dict[str, Any]] = field(default_factory=list)
    _i: int = 0

    async def __call__(self, **kwargs: Any) -> FakeCompletion:
        self.calls.append(kwargs)
        reply = self.replies[self._i]
        self._i += 1
        return reply


def _json_replies(*objs: Any) -> list[FakeCompletion]:
    return [_completion(content=json.dumps(o)) for o in objs]


# --------------------------------------------------------------------------- #
# Pure helpers.
# --------------------------------------------------------------------------- #
def test_split_model_prefix_bare_and_multicolon() -> None:
    assert _split_model("openai:gpt-4o", "anthropic") == ("openai", "gpt-4o")
    assert _split_model("claude-opus-4-8", "anthropic") == ("anthropic", "claude-opus-4-8")
    # split on the FIRST colon only (ollama tags carry their own colon)
    assert _split_model("ollama:llama3:8b", "anthropic") == ("ollama", "llama3:8b")


def test_strip_code_fence() -> None:
    assert _strip_code_fence('{"a": 1}') == '{"a": 1}'
    assert _strip_code_fence('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _strip_code_fence('```\n{"a": 1}\n```') == '{"a": 1}'


# --------------------------------------------------------------------------- #
# Routing + message assembly.
# --------------------------------------------------------------------------- #
def test_caller_routes_provider_model_and_builds_messages() -> None:
    rec = Recorder(_json_replies({"output": "ok"}))
    reasoner = Reasoner(name="b1", model="openai:gpt-4o", system="be terse")
    caller = make_llm_caller(acompletion=rec)

    run(caller(reasoner, {"input": "hi", "trace": []}))

    call = rec.calls[0]
    assert call["provider"] == "openai" and call["model"] == "gpt-4o"
    assert call["messages"][0] == {"role": "system", "content": "be terse"}
    # non-string value is JSON-encoded into the user turn
    assert call["messages"][1] == {"role": "user", "content": json.dumps({"input": "hi", "trace": []})}
    assert "response_format" not in call  # no reply_schema => no structured request


def test_bare_model_falls_back_to_default_provider() -> None:
    rec = Recorder(_json_replies({"output": "ok"}))
    reasoner = Reasoner(name="b2", model="claude-opus-4-8")
    run(make_llm_caller(default_provider="anthropic", acompletion=rec)(reasoner, "hello"))
    assert rec.calls[0]["provider"] == "anthropic"
    assert rec.calls[0]["model"] == "claude-opus-4-8"
    # string value passes through verbatim (not double-encoded)
    assert rec.calls[0]["messages"][-1] == {"role": "user", "content": "hello"}


def test_temperature_passthrough() -> None:
    rec = Recorder(_json_replies({"output": "ok"}))
    reasoner = Reasoner(name="b3", model="openai:gpt-4o", temperature=0.2)
    run(make_llm_caller(acompletion=rec)(reasoner, "x"))
    assert rec.calls[0]["temperature"] == 0.2


def test_qos_request_field_openai_per_tier() -> None:
    reasoner = Reasoner(name="t", model="openai:gpt-x", system="s")

    rec = Recorder([_completion(content="ok")])
    run(complete_reasoner(reasoner, "hi", acompletion=rec, dispatch=ReasonerDispatch(qos=QoSTier.PRIORITY)))
    assert rec.calls[-1].get("service_tier") == "priority"

    rec = Recorder([_completion(content="ok")])
    run(complete_reasoner(reasoner, "hi", acompletion=rec, dispatch=ReasonerDispatch(qos=QoSTier.STANDARD)))
    assert "service_tier" not in rec.calls[-1]

    rec = Recorder([_completion(content="ok")])
    run(complete_reasoner(reasoner, "hi", acompletion=rec, dispatch=ReasonerDispatch(qos=QoSTier.FLEX)))
    assert rec.calls[-1].get("service_tier") == "flex"


def test_qos_request_field_anthropic_per_tier() -> None:
    reasoner = Reasoner(name="t", model="anthropic:claude-x", system="s")

    rec = Recorder([_completion(content="ok")])
    run(complete_reasoner(reasoner, "hi", acompletion=rec, dispatch=ReasonerDispatch(qos=QoSTier.PRIORITY)))
    assert rec.calls[-1].get("service_tier") == "priority"

    rec = Recorder([_completion(content="ok")])
    run(complete_reasoner(reasoner, "hi", acompletion=rec, dispatch=ReasonerDispatch(qos=QoSTier.STANDARD)))
    assert "service_tier" not in rec.calls[-1]

    rec = Recorder([_completion(content="ok")])
    run(complete_reasoner(reasoner, "hi", acompletion=rec, dispatch=ReasonerDispatch(qos=QoSTier.FLEX)))
    assert rec.calls[-1].get("service_tier") == "standard_only"


def test_qos_batch_rejected_by_complete_reasoner() -> None:
    rec = Recorder([_completion(content="ok")])
    reasoner = Reasoner(name="t", model="openai:gpt-x", system="s")

    with pytest.raises(ValueError, match="BATCH must not reach complete_reasoner"):
        run(complete_reasoner(reasoner, "hi", acompletion=rec, dispatch=ReasonerDispatch(qos=QoSTier.BATCH)))


def test_complete_reasoner_default_dispatch_sets_no_tier_field() -> None:
    rec = Recorder([_completion(content="ok")])
    reasoner = Reasoner(name="t", model="openai:gpt-x", system="s")

    run(complete_reasoner(reasoner, "hi", acompletion=rec))

    assert "service_tier" not in rec.calls[-1]


# --------------------------------------------------------------------------- #
# Structured output strategy (Q3).
# --------------------------------------------------------------------------- #
_DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"tool": {"type": "string"}, "input": {}},
}


def test_schema_uses_native_response_format_for_standard_provider() -> None:
    rec = Recorder(_json_replies({"tool": "search", "input": "q"}))
    reasoner = Reasoner(name="b4", model="openai:gpt-4o", system="sys", reply=_DECISION_SCHEMA)
    run(make_llm_caller(acompletion=rec)(reasoner, "x"))

    call = rec.calls[0]
    assert call["response_format"]["type"] == "json_schema"
    assert call["response_format"]["json_schema"]["schema"] == _DECISION_SCHEMA
    # native path leaves the system prompt clean (schema not injected as prose)
    assert call["messages"][0]["content"] == "sys"


def test_fallback_provider_uses_prompt_injection_not_response_format() -> None:
    rec = Recorder(_json_replies({"tool": "search", "input": "q"}))
    reasoner = Reasoner(name="b5", model="gemini:gemini-2.0", system="sys", reply=_DECISION_SCHEMA)
    run(make_llm_caller(acompletion=rec)(reasoner, "x"))

    call = rec.calls[0]
    assert "response_format" not in call
    # schema is injected into the system turn instead
    assert json.dumps(_DECISION_SCHEMA) in call["messages"][0]["content"]
    assert "sys" in call["messages"][0]["content"]


def test_native_failure_retries_with_prompt_injection() -> None:
    class Flaky:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        async def __call__(self, **kwargs: Any) -> FakeCompletion:
            self.calls.append(kwargs)
            if "response_format" in kwargs:
                raise RuntimeError("provider rejects response_format")
            return _completion(content=json.dumps({"output": "ok"}))

    flaky = Flaky()
    reasoner = Reasoner(name="b6", model="openai:gpt-4o", system="sys", reply=_DECISION_SCHEMA)
    reply = run(make_llm_caller(acompletion=flaky)(reasoner, "x")).reply

    assert reply == {"output": "ok"}
    assert len(flaky.calls) == 2  # native attempt, then prompt-injected retry
    assert "response_format" in flaky.calls[0]
    assert "response_format" not in flaky.calls[1]
    assert json.dumps(_DECISION_SCHEMA) in flaky.calls[1]["messages"][0]["content"]


# --------------------------------------------------------------------------- #
# Reply parsing.
# --------------------------------------------------------------------------- #
def test_reply_json_parsed_and_interpreted_as_call() -> None:
    rec = Recorder([_completion(content='```json\n{"tool": "search", "input": "q"}\n```')])
    reasoner = Reasoner(name="b7", model="openai:gpt-4o", reply=_DECISION_SCHEMA)
    reply = run(make_llm_caller(acompletion=rec)(reasoner, "x")).reply

    assert reply == {"tool": "search", "input": "q"}
    action = interpret_reasoner_reply(reply)
    assert action.decision is Decision.CALL
    assert action.payload == {"tool": "search", "input": "q"}


def test_parsed_field_preferred_over_content() -> None:
    rec = Recorder([_completion(parsed={"output": "structured"})])
    reasoner = Reasoner(name="b8", model="openai:gpt-4o", reply=_DECISION_SCHEMA)
    assert run(make_llm_caller(acompletion=rec)(reasoner, "x")).reply == {"output": "structured"}


def test_no_schema_returns_raw_text() -> None:
    rec = Recorder([_completion(content="just prose")])
    reasoner = Reasoner(name="b9", model="openai:gpt-4o")
    assert run(make_llm_caller(acompletion=rec)(reasoner, "x")).reply == "just prose"


def test_unparseable_json_with_schema_returns_raw_for_controller_error() -> None:
    rec = Recorder([_completion(content="not json at all")])
    reasoner = Reasoner(name="b10", model="openai:gpt-4o", reply=_DECISION_SCHEMA)
    reply = run(make_llm_caller(acompletion=rec)(reasoner, "x")).reply
    # raw string flows through; strict interpretation flags it cleanly
    assert reply == "not json at all"
    assert interpret_reasoner_reply(reply).decision is Decision.CONTROLLER_ERROR


# --------------------------------------------------------------------------- #
# Facade seam: make_local_reasoner resolves the registered Reasoner by name.
# --------------------------------------------------------------------------- #
def test_make_local_reasoner_resolves_registered_reasoner() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="resolver_reasoner", model="openai:gpt-4o", system="resolved-system"))
    rec = Recorder(_json_replies({"output": "ok"}))
    local = make_local_reasoner(acompletion=rec)

    run(local("resolver_reasoner", {"input": "hi", "trace": []}))

    assert rec.calls[0]["provider"] == "openai"
    assert rec.calls[0]["messages"][0]["content"] == "resolved-system"


def test_make_local_reasoner_preserves_business_tools_input() -> None:
    DEFAULT_REGISTRY.register_reasoner(Reasoner(name="business_tools_reasoner", model="openai:gpt-4o"))
    rec = Recorder(_json_replies({"output": "ok"}))
    local = make_local_reasoner(acompletion=rec)
    payload = {"tools": ["a", "b"], "q": "x"}

    run(local("business_tools_reasoner", payload))

    call = rec.calls[0]
    assert "tools" not in call
    assert json.loads(call["messages"][-1]["content"]) == payload


def test_agent_facade_drives_real_loop_through_local_reasoner() -> None:
    """End-to-end: a real provider caller drives the facade's local loop, proving
    both the make_local_reasoner seam and the facade passing the reasoner *name*."""

    @tool(effect="read", idempotent=True)
    def lookup(q: str) -> dict[str, str]:
        return {"hit": f"answer-for-{q}"}

    rec = Recorder(
        _json_replies(
            {"tool": "lookup", "input": "widgets"},
            {"output": {"answer": "done"}},
        )
    )
    agent = Agent(
        "openai:gpt-4o",
        tools=[lookup],
        name="multi_provider_facade_agent",
        instructions="Look one thing up, then answer.",
        llm=make_local_reasoner(acompletion=rec),
        budget_cost=20.0,
    )

    result = agent.run("start")

    assert result.status == "done"
    assert result.output == {"answer": "done"}
    assert [t["decision"] for t in result["trace"]] == ["call"]
    assert [t["ref"] for t in result["trace"]] == ["lookup"]
    # the model was reached once per round (call round + finish round)
    assert len(rec.calls) == 2
    assert rec.calls[0]["provider"] == "openai" and rec.calls[0]["model"] == "gpt-4o"


def test_complete_reasoner_direct_is_provider_agnostic() -> None:
    rec = Recorder(_json_replies({"output": "ok"}))
    reasoner = Reasoner(name="b11", model="mistral:mistral-small", system="s", reply=_DECISION_SCHEMA)
    reply = run(complete_reasoner(reasoner, "v", acompletion=rec, default_provider="anthropic")).reply
    assert reply == {"output": "ok"}
    assert rec.calls[0]["provider"] == "mistral" and rec.calls[0]["model"] == "mistral-small"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
