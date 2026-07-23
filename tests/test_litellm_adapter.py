from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from conftest import run
from julep.dotctx import Reasoner
from julep.errors import ResilienceExhausted
from julep.execution.llm_result import LlmCallMeta, LlmResult
from julep.llm import litellm_caller, prepare_litellm_payload, with_model_ladder
from julep.qos import ReasonerDispatch
from julep.resilience import AttemptRecord


def _completion(content: str = "ok") -> Any:
    message = SimpleNamespace(content=content, parsed=None)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice], usage=None, model="served")


def test_prepare_litellm_payload_maps_provider_reasoning_contracts() -> None:
    openrouter = prepare_litellm_payload(
        {"model": "openrouter:openai/gpt-5@high", "reasoning_effort": "low"}
    )
    assert openrouter["model"] == "openrouter/openai/gpt-5"
    assert openrouter["extra_body"] == {"reasoning": {"effort": "high"}}
    assert "reasoning_effort" not in openrouter

    anthropic = prepare_litellm_payload(
        {"model": "anthropic:claude-sonnet-4-6", "reasoning_effort": "medium"}
    )
    assert anthropic["thinking"] == {"type": "enabled", "budget_tokens": 2048}
    assert anthropic["temperature"] == 1.0
    assert "reasoning_effort" not in anthropic

    fireworks = prepare_litellm_payload(
        {"model": "fireworks:accounts/acme/deployments/model", "reasoning_effort": "low"}
    )
    assert fireworks["model"] == "fireworks_ai/accounts/acme/deployments/model"
    assert fireworks["reasoning_effort"] == "low"


def test_prepare_litellm_payload_clamps_direct_openai_gpt5_temperature() -> None:
    prepared = prepare_litellm_payload(
        {
            "model": "openai:gpt-5.4-mini",
            "reasoning_effort": "high",
            "temperature": 0.2,
        }
    )
    assert prepared["model"] == "openai/gpt-5.4-mini"
    assert prepared["temperature"] == 1.0
    assert prepared["allowed_openai_params"] == ["reasoning_effort"]


def test_litellm_caller_is_canonical_and_injectable() -> None:
    seen: dict[str, Any] = {}

    async def fake_acompletion(**kwargs: Any) -> Any:
        seen.update(kwargs)
        return _completion()

    caller = litellm_caller(request_timeout_s=17.0, acompletion=fake_acompletion)
    reasoner = Reasoner(
        name="summary",
        model="openrouter:openai/gpt-5",
        reasoning_effort="high",
    )
    result = run(
        caller(
            reasoner,
            {"text": "hello"},
            None,
            None,
            ReasonerDispatch(),
            tools=[{"type": "function", "function": {"name": "lookup"}}],
            parallel_tool_calls=False,
        )
    )
    assert result.reply == "ok"
    assert seen["model"] == "openrouter/openai/gpt-5"
    assert seen["extra_body"] == {"reasoning": {"effort": "high"}}
    assert seen["timeout"] == 17.0
    assert seen["tools"] == [{"type": "function", "function": {"name": "lookup"}}]
    assert seen["parallel_tool_calls"] is False


class HttpError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}")


def test_model_ladder_advances_only_for_provider_transient_errors() -> None:
    calls: list[tuple[str, str | None]] = []
    attempts: list[AttemptRecord] = []

    async def base(reasoner: Reasoner, *_args: Any) -> Any:
        calls.append((reasoner.model, reasoner.reasoning_effort))
        if len(calls) == 1:
            raise HttpError(503)
        return LlmResult(
            "rescued",
            LlmCallMeta(served_model=reasoner.model, provider="anthropic"),
        )

    caller = with_model_ladder(
        base,
        models=["anthropic:claude-sonnet-4-6@medium"],
        on_attempt=attempts.append,
    )
    result = run(caller(Reasoner("r", "openai:gpt-5@low"), "value"))
    assert result.reply == "rescued"
    assert calls == [
        ("openai:gpt-5", "low"),
        ("anthropic:claude-sonnet-4-6", "medium"),
    ]
    assert [item.outcome for item in attempts] == ["transient", "ok"]
    assert [item.outcome for item in result.meta.attempts] == ["transient", "ok"]


def test_model_ladder_fails_fast_on_configuration_error() -> None:
    calls: list[str] = []

    async def base(reasoner: Reasoner, *_args: Any) -> Any:
        calls.append(reasoner.model)
        raise HttpError(401)

    caller = with_model_ladder(base, models=["anthropic:fallback"])
    with pytest.raises(HttpError):
        run(caller(Reasoner("r", "openai:primary"), "value"))
    assert calls == ["openai:primary"]


def test_model_ladder_exhaustion_keeps_attempt_provenance() -> None:
    async def base(_reasoner: Reasoner, *_args: Any) -> Any:
        raise TimeoutError("slow")

    caller = with_model_ladder(base, models=["anthropic:fallback"])
    with pytest.raises(ResilienceExhausted) as excinfo:
        run(caller(Reasoner("r", "openai:primary"), "value"))
    assert [item.model for item in excinfo.value.attempts] == [
        "openai:primary",
        "anthropic:fallback",
    ]


def test_model_ladder_forwards_native_tool_options() -> None:
    seen: dict[str, Any] = {}

    async def base(_reasoner: Reasoner, _value: Any, *_args: Any, **kwargs: Any) -> str:
        seen.update(kwargs)
        return "ok"

    caller = with_model_ladder(base, models=[])
    result = run(
        caller(
            Reasoner("r", "openai:primary"),
            "value",
            tools=[{"type": "function", "function": {"name": "lookup"}}],
            parallel_tool_calls=True,
        )
    )
    assert result == "ok"
    assert seen == {
        "tools": [{"type": "function", "function": {"name": "lookup"}}],
        "parallel_tool_calls": True,
    }
