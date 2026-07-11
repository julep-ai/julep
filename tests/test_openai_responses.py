"""GPT-5.6 routing and OpenAI Responses adapter coverage."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import pytest

from conftest import run
from julep import Agent, tool
from julep.dotctx import Reasoner
from julep.execution.llm import (
    complete_reasoner,
    make_llm_caller,
    make_local_reasoner,
    make_resilient_llm_caller,
)
from julep.execution.openai_responses import (
    ResponsesModelBehaviorError,
    ResponsesRefusalError,
    ResponsesStatusError,
    responses_input,
    responses_tool_defs,
    uses_openai_responses,
)
from julep.resilience import AttemptRecord, ResiliencePolicy


@dataclass
class FakeFunctionCall:
    call_id: str
    name: str
    arguments: str
    type: str = "function_call"


@dataclass
class FakeText:
    text: str
    type: str = "output_text"


@dataclass
class FakeMessage:
    content: list[Any]
    type: str = "message"


@dataclass
class FakeRefusal:
    refusal: str
    type: str = "refusal"


@dataclass
class FakeInputDetails:
    cached_tokens: int = 0


@dataclass
class FakeUsage:
    input_tokens: int = 11
    output_tokens: int = 7
    total_tokens: int = 18
    input_tokens_details: FakeInputDetails = field(default_factory=FakeInputDetails)


@dataclass
class FakeResponse:
    output: list[Any]
    model: str = "gpt-5.6-sol"
    usage: FakeUsage = field(default_factory=FakeUsage)
    status: str = "completed"
    error: Any = None
    incomplete_details: Any = None


@dataclass
class Recorder:
    reply: Any
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def __call__(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.reply


def _tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_weather",
                "description": "Look up weather for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                    "additionalProperties": False,
                },
            },
        }
    ]


@pytest.mark.parametrize(
    "model",
    ["gpt-5.6", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.6-sol-2026-07-10"],
)
def test_gpt_5_6_family_uses_responses(model: str) -> None:
    assert uses_openai_responses("openai", model)


def test_other_models_and_providers_keep_completion_transport() -> None:
    assert not uses_openai_responses("openai", "gpt-5.5")
    assert not uses_openai_responses("openai", "gpt-4o")
    assert not uses_openai_responses("other", "gpt-5.6-sol")


def test_complete_reasoner_routes_gpt_5_6_tools_to_responses() -> None:
    async def unexpected_completion(**kwargs: Any) -> Any:
        raise AssertionError(f"acompletion must not be called: {kwargs}")

    responses = Recorder(
        FakeResponse(
            output=[
                FakeFunctionCall(
                    call_id="call-1",
                    name="lookup_weather",
                    arguments='{"city":"Paris"}',
                )
            ]
        )
    )
    reasoner = Reasoner(
        name="responses-tools",
        model="openai:gpt-5.6-sol",
        system="Use the weather tool.",
        reasoning_effort="low",
        max_tokens=64,
    )

    result = run(
        complete_reasoner(
            reasoner,
            "Weather in Paris?",
            acompletion=unexpected_completion,
            aresponses=responses,
            tools=_tools(),
            parallel_tool_calls=False,
        )
    )

    call = responses.calls[0]
    assert call["provider"] == "openai" and call["model"] == "gpt-5.6-sol"
    assert call["store"] is False
    assert call["reasoning"] == {"context": "current_turn", "effort": "low"}
    assert call["max_output_tokens"] == 64
    assert call["parallel_tool_calls"] is False
    assert call["tools"] == [
        {
            "type": "function",
            "name": "lookup_weather",
            "description": "Look up weather for a city.",
            "parameters": _tools()[0]["function"]["parameters"],
            "strict": False,
        }
    ]
    assert call["input_data"] == [
        {"role": "system", "content": "Use the weather tool."},
        {"role": "user", "content": "Weather in Paris?"},
    ]
    assert result.reply == {
        "tool_calls": [
            {"id": "call-1", "tool": "lookup_weather", "input": {"city": "Paris"}}
        ]
    }
    assert result.meta.native_tool_calls == 1
    assert result.meta.input_tokens == 11
    assert result.meta.output_tokens == 7


def test_responses_transcript_maps_calls_and_outputs() -> None:
    assert responses_input(
        [
            {"role": "user", "content": "Weather?"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "lookup_weather",
                            "arguments": '{"city":"Paris"}',
                        },
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call-1", "content": '{"temp":25}'},
        ]
    ) == [
        {"role": "user", "content": "Weather?"},
        {
            "type": "function_call",
            "call_id": "call-1",
            "name": "lookup_weather",
            "arguments": '{"city":"Paris"}',
        },
        {
            "type": "function_call_output",
            "call_id": "call-1",
            "output": '{"temp":25}',
        },
    ]


def test_responses_transcript_uses_provider_safe_aliases_and_collision_suffixes() -> None:
    tools = [
        {
            "type": "function",
            "function": {"name": "srv/x", "parameters": {"type": "string"}},
        },
        {
            "type": "function",
            "function": {
                "name": "srv_x",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]
    responses = Recorder(FakeResponse(output=[FakeMessage(content=[FakeText("ok")])]))
    transcript = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "srv/x", "arguments": '"Paris"'},
                },
                {
                    "id": "call-2",
                    "type": "function",
                    "function": {"name": "srv_x", "arguments": "{}"},
                },
            ],
        },
        {"role": "tool", "tool_call_id": "call-1", "content": "first"},
        {"role": "tool", "tool_call_id": "call-2", "content": "second"},
    ]

    result = run(
        complete_reasoner(
            Reasoner(name="responses-aliases", model="openai:gpt-5.6-sol"),
            "continue",
            aresponses=responses,
            tools=tools,
            transcript=transcript,
        )
    )

    assert result.reply == "ok"
    call = responses.calls[0]
    assert [tool["name"] for tool in call["tools"]] == ["srv_x", "srv_x_2"]
    replayed_calls = [
        item for item in call["input_data"] if item.get("type") == "function_call"
    ]
    assert [(item["name"], item["arguments"]) for item in replayed_calls] == [
        ("srv_x", '{"value": "Paris"}'),
        ("srv_x_2", "{}"),
    ]


def test_responses_wraps_scalar_tool_schema_and_restores_bare_argument() -> None:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "lookup_scalar",
                "description": "Look up a city.",
                "parameters": {"type": "string"},
            },
        }
    ]
    assert responses_tool_defs(tools) == [
        {
            "type": "function",
            "name": "lookup_scalar",
            "description": "Look up a city.",
            "parameters": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
                "additionalProperties": False,
            },
            "strict": False,
        }
    ]
    responses = Recorder(
        FakeResponse(
            output=[
                FakeFunctionCall(
                    call_id="call-scalar",
                    name="lookup_scalar",
                    arguments='{"value":"Paris"}',
                )
            ]
        )
    )
    result = run(
        complete_reasoner(
            Reasoner(name="responses-scalar", model="openai:gpt-5.6-sol"),
            "Look up Paris.",
            aresponses=responses,
            tools=tools,
        )
    )
    assert result.reply["tool_calls"][0]["input"] == "Paris"

    assert responses_input(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-scalar",
                        "type": "function",
                        "function": {"name": "lookup_scalar", "arguments": '"Paris"'},
                    }
                ],
            }
        ],
        {"lookup_scalar"},
    ) == [
        {
            "type": "function_call",
            "call_id": "call-scalar",
            "name": "lookup_scalar",
            "arguments": '{"value": "Paris"}',
        }
    ]


def test_responses_structured_text_and_format_are_normalized() -> None:
    responses = Recorder(
        FakeResponse(output=[FakeMessage(content=[FakeText('{"answer":"ok"}')])])
    )
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    }
    result = run(
        complete_reasoner(
            Reasoner(name="responses-json", model="openai:gpt-5.6", reply=schema),
            "Answer.",
            aresponses=responses,
        )
    )

    assert result.reply == {"answer": "ok"}
    assert responses.calls[0]["response_format"] == {
        "type": "json_schema",
        "name": "reply",
        "schema": schema,
        "strict": False,
    }


def test_responses_schema_prompted_tool_round_strips_json_fences() -> None:
    responses = Recorder(
        FakeResponse(output=[FakeMessage(content=[FakeText('```json\n{"answer":"ok"}\n```')])])
    )
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    }

    result = run(
        complete_reasoner(
            Reasoner(name="responses-fenced-json", model="openai:gpt-5.6", reply=schema),
            "Answer without calling a tool.",
            aresponses=responses,
            tools=_tools(),
        )
    )

    assert result.reply == {"answer": "ok"}
    assert "response_format" not in responses.calls[0]


def test_pre_5_6_openai_stays_on_acompletion() -> None:
    completion = Recorder(
        type(
            "Completion",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Message", (), {"content": "ok", "parsed": None})()},
                    )()
                ]
            },
        )()
    )

    async def unexpected_responses(**kwargs: Any) -> Any:
        raise AssertionError(f"aresponses must not be called: {kwargs}")

    result = run(
        complete_reasoner(
            Reasoner(name="chat", model="openai:gpt-5.5"),
            "hi",
            acompletion=completion,
            aresponses=unexpected_responses,
        )
    )
    assert result.reply == "ok"
    assert completion.calls[0]["model"] == "gpt-5.5"


def test_incomplete_failed_and_refused_responses_raise() -> None:
    incomplete = Recorder(
        FakeResponse(output=[], status="incomplete", incomplete_details={"reason": "max"})
    )
    with pytest.raises(ResponsesModelBehaviorError, match="incomplete"):
        run(
            complete_reasoner(
                Reasoner(name="incomplete", model="openai:gpt-5.6-sol"),
                "hi",
                aresponses=incomplete,
            )
        )

    failed = Recorder(FakeResponse(output=[], status="failed", error={"message": "down"}))
    with pytest.raises(ResponsesStatusError, match="failed"):
        run(
            complete_reasoner(
                Reasoner(name="failed", model="openai:gpt-5.6-sol"),
                "hi",
                aresponses=failed,
            )
        )

    refused = Recorder(
        FakeResponse(output=[FakeMessage(content=[FakeRefusal("not allowed")])])
    )
    with pytest.raises(ResponsesRefusalError, match="model refusal"):
        run(
            complete_reasoner(
                Reasoner(name="refused", model="openai:gpt-5.6-sol"),
                "hi",
                aresponses=refused,
            )
        )


def test_resilient_caller_advances_on_responses_model_behavior() -> None:
    responses = Recorder(
        FakeResponse(output=[], status="incomplete", incomplete_details={"reason": "max"})
    )
    completion = Recorder(
        type(
            "Completion",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Message", (), {"content": "rescued", "parsed": None})()},
                    )()
                ]
            },
        )()
    )
    attempts: list[AttemptRecord] = []
    caller = make_resilient_llm_caller(
        policy=ResiliencePolicy(
            fallbacks={"openai:gpt-5.6-sol": ("openai:gpt-5.5",)},
            transient_attempts=3,
        ),
        acompletion=completion,
        aresponses=responses,
        on_attempt=attempts.append,
    )

    result = run(
        caller(Reasoner(name="resilient-responses", model="openai:gpt-5.6-sol"), "hi")
    )

    assert result.reply == "rescued"
    assert [(attempt.model, attempt.outcome) for attempt in attempts] == [
        ("openai:gpt-5.6-sol", "model_behavior"),
        ("openai:gpt-5.5", "ok"),
    ]
    assert len(responses.calls) == 1


def test_resilient_caller_fails_closed_on_responses_refusal() -> None:
    responses = Recorder(
        FakeResponse(output=[FakeMessage(content=[FakeRefusal("not allowed")])])
    )
    completion = Recorder(
        type(
            "Completion",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Message", (), {"content": "unsafe", "parsed": None})()},
                    )()
                ]
            },
        )()
    )
    attempts: list[AttemptRecord] = []
    caller = make_resilient_llm_caller(
        policy=ResiliencePolicy(
            fallbacks={"openai:gpt-5.6-sol": ("openai:gpt-5.5",)},
        ),
        acompletion=completion,
        aresponses=responses,
        on_attempt=attempts.append,
    )

    with pytest.raises(ResponsesRefusalError, match="model refusal"):
        run(
            caller(
                Reasoner(name="resilient-refusal", model="openai:gpt-5.6-sol"),
                "hi",
            )
        )

    assert [(attempt.model, attempt.outcome) for attempt in attempts] == [
        ("openai:gpt-5.6-sol", "model_behavior"),
    ]
    assert completion.calls == []


@pytest.mark.live
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY is required for the live GPT-5.6 Responses smoke",
)
def test_live_gpt_5_6_tool_call_through_julep_builder() -> None:
    result = run(
        make_llm_caller()(
            Reasoner(
                name="live-gpt-5.6-responses",
                model="openai:gpt-5.6-sol",
                system="Always call lookup_weather for the requested city.",
                reasoning_effort="low",
                max_tokens=64,
            ),
            "What is the weather in Paris?",
            tools=_tools(),
            parallel_tool_calls=False,
        )
    )
    assert result.reply["tool_calls"][0]["tool"] == "lookup_weather"
    assert result.reply["tool_calls"][0]["input"] == {"city": "Paris"}
    assert result.meta.served_model == "gpt-5.6-sol"
    assert result.meta.native_tool_calls == 1


@pytest.mark.live
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY is required for the live GPT-5.6 agent smoke",
)
def test_live_gpt_5_6_native_agent_executes_tool_and_finishes() -> None:
    @tool(effect="read", idempotent=True, name="live_responses_weather")
    def weather(city: str) -> dict[str, Any]:
        return {"city": city, "temperature": 25, "unit": "C"}

    agent = Agent(
        "openai:gpt-5.6-sol",
        tools=[weather],
        name="live_gpt_5_6_responses_agent",
        instructions=(
            "Call live_responses_weather exactly once for the requested city. "
            "After receiving its result, finish with an object containing city, "
            "temperature, and unit. Never call a tool already present in the trace."
        ),
        native_tools=True,
        reasoning_effort="low",
        max_tokens=128,
        max_rounds=4,
        llm=make_local_reasoner(),
    )

    result = run(agent.arun("What is the weather in Paris?"))

    assert result.status == "done"
    assert result.output == {"city": "Paris", "temperature": 25, "unit": "C"}
    assert [entry["decision"] for entry in result.trace] == ["call"]
