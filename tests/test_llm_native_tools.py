"""Target tests for native provider tool-call passthrough.

No network and no any-llm install: each test injects a fake ``acompletion``
shaped like any-llm's OpenAI-typed completion. These tests are intentionally
ahead of the implementation and currently fail on the missing passthrough seam.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from julep.dotctx import Reasoner
from julep.execution.llm import (
    complete_reasoner,
    make_llm_caller,
    make_resilient_llm_caller,
    provider_safe_tool_defs,
    provider_safe_tool_name,
)
from julep.execution.llm_result import LlmCallMeta
from julep.resilience import ResiliencePolicy
from conftest import run


# --------------------------------------------------------------------------- #
# Fakes shaped like any-llm's OpenAI-typed completion.
# --------------------------------------------------------------------------- #
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


def _completion(
    content: Optional[str] = None,
    parsed: Any = None,
    tool_calls: Optional[list[FakeToolCall]] = None,
) -> FakeCompletion:
    return FakeCompletion(
        choices=[FakeChoice(FakeMessage(content=content, parsed=parsed, tool_calls=tool_calls))]
    )


def _tool_call(call_id: str, name: str, arguments: str) -> FakeToolCall:
    return FakeToolCall(id=call_id, function=FakeFunction(name=name, arguments=arguments))


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


_REPLY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
}


def _tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search",
                "parameters": {
                    "type": "object",
                    "properties": {"q": {"type": "string"}},
                    "required": ["q"],
                },
            },
        }
    ]


def test_tools_and_parallel_tool_calls_forwarded_verbatim() -> None:
    rec = Recorder([_completion(content="ok")])
    reasoner = Reasoner(name="nt1", model="openai:gpt-4o", system="sys")
    tools = _tools()

    run(
        complete_reasoner(
            reasoner,
            "x",
            acompletion=rec,
            tools=tools,
            parallel_tool_calls=False,
        )
    )

    call = rec.calls[0]
    assert call["tools"] is tools
    assert call["parallel_tool_calls"] is False


def test_mcp_style_tool_names_are_provider_safe_and_reversed() -> None:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "srv/double",
                "parameters": {"type": "object"},
            },
        }
    ]
    safe = provider_safe_tool_name("srv/double")
    assert "/" not in safe
    assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", safe)
    rec = Recorder([
        _completion(tool_calls=[_tool_call("c1", safe, '{"n": 2}')])
    ])

    result = run(
        make_llm_caller(acompletion=rec)(
            Reasoner(name="mcp_nt", model="openai:gpt-4o", system="s"),
            "x",
            tools=tools,
        )
    )

    provider_name = rec.calls[0]["tools"][0]["function"]["name"]
    assert provider_name == safe
    assert "/" not in provider_name
    assert result.reply["tool_calls"][0]["tool"] == "srv/double"
    assert result.reply["tool_calls"][0]["input"] == {"n": 2}


def test_provider_safe_tool_defs_identity_when_all_names_safe() -> None:
    tools = _tools()

    safe_tools, reverse = provider_safe_tool_defs(tools)

    assert safe_tools is tools
    assert reverse == {}


def test_provider_safe_tool_defs_disambiguates_collisions() -> None:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "srv/x",
                "parameters": {"type": "object"},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "srv_x",
                "parameters": {"type": "object"},
            },
        },
    ]

    safe_tools, reverse = provider_safe_tool_defs(tools)
    safe_names = [tool["function"]["name"] for tool in safe_tools]

    assert len(set(safe_names)) == 2
    assert all("/" not in name for name in safe_names)
    assert reverse[safe_names[0]] == "srv/x"
    assert reverse[safe_names[1]] == "srv_x"


def test_tool_calls_reply_normalized_and_counted_in_order() -> None:
    rec = Recorder([
        _completion(
            tool_calls=[
                _tool_call("c1", "search", '{"q": "x"}'),
                _tool_call("c2", "fetch", '{"url": "y"}'),
            ]
        )
    ])
    reasoner = Reasoner(name="nt2", model="openai:gpt-4o", system="sys")
    tools = _tools()

    result = run(make_llm_caller(acompletion=rec)(reasoner, "x", tools=tools))

    assert result.reply == {
        "tool_calls": [
            {"id": "c1", "tool": "search", "input": {"q": "x"}},
            {"id": "c2", "tool": "fetch", "input": {"url": "y"}},
        ]
    }
    assert result.meta.native_tool_calls == 2


def test_invalid_tool_call_arguments_are_kept_as_raw_input() -> None:
    rec = Recorder([
        _completion(tool_calls=[_tool_call("c1", "search", "{not json")])
    ])
    reasoner = Reasoner(name="nt3", model="openai:gpt-4o", system="sys")

    result = run(
        make_llm_caller(acompletion=rec)(reasoner, "x", tools=_tools())
    )

    assert result.reply == {
        "tool_calls": [
            {"id": "c1", "tool": "search", "input": "{not json"},
        ]
    }
    assert result.meta.native_tool_calls == 1


def test_no_tool_calls_with_reply_schema_still_parses_text_json_when_tools_passed() -> None:
    rec = Recorder([_completion(content=json.dumps({"answer": "ok"}))])
    reasoner = Reasoner(
        name="nt4",
        model="openai:gpt-4o",
        system="sys",
        reply=_REPLY_SCHEMA,
    )

    result = run(
        make_llm_caller(acompletion=rec)(reasoner, "x", tools=_tools())
    )

    assert result.reply == {"answer": "ok"}
    assert result.meta.native_tool_calls == 0


def test_tools_none_sends_no_tools_kwarg() -> None:
    rec = Recorder([_completion(content="ok")])
    reasoner = Reasoner(name="nt5", model="openai:gpt-4o", system="sys")

    run(complete_reasoner(reasoner, "x", acompletion=rec, tools=None))

    assert "tools" not in rec.calls[0]


def test_reply_schema_with_tools_uses_prompt_schema_hint_not_response_format() -> None:
    rec = Recorder([_completion(content=json.dumps({"answer": "ok"}))])
    reasoner = Reasoner(
        name="nt6",
        model="openai:gpt-4o",
        system="sys",
        reply=_REPLY_SCHEMA,
    )
    tools = _tools()

    run(
        complete_reasoner(
            reasoner,
            "x",
            acompletion=rec,
            tools=tools,
            parallel_tool_calls=True,
        )
    )

    call = rec.calls[0]
    assert call["tools"] is tools
    assert call["parallel_tool_calls"] is True
    assert "response_format" not in call
    assert "Reply with a single JSON object" in call["messages"][0]["content"]


def test_native_tool_calls_meta_to_attrs_emits_only_when_positive() -> None:
    meta = LlmCallMeta(served_model="gpt-4o", provider="openai", native_tool_calls=2)
    assert meta.native_tool_calls == 2
    assert meta.to_attrs()["llm.tool_calls"] == 2

    plain = LlmCallMeta(served_model="gpt-4o", provider="openai")
    assert plain.native_tool_calls == 0
    assert "llm.tool_calls" not in plain.to_attrs()


def test_resilient_llm_caller_forwards_tools_and_normalizes_tool_calls() -> None:
    rec = Recorder([
        _completion(tool_calls=[_tool_call("c1", "search", '{"q": "x"}')])
    ])
    caller = make_resilient_llm_caller(
        policy=ResiliencePolicy(fallbacks={}),
        acompletion=rec,
    )
    reasoner = Reasoner(name="nt8", model="openai:gpt-4o", system="sys")
    tools = _tools()

    result = run(
        caller(
            reasoner,
            "x",
            tools=tools,
            parallel_tool_calls=True,
        )
    )

    call = rec.calls[0]
    assert call["tools"] is tools
    assert call["parallel_tool_calls"] is True
    assert result.reply == {
        "tool_calls": [
            {"id": "c1", "tool": "search", "input": {"q": "x"}},
        ]
    }
    assert result.meta.native_tool_calls == 1
