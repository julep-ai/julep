from __future__ import annotations

import asyncio
import importlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional

import pytest

from julep import Agent, HAVE_TEMPORAL, Reasoner, get_reasoner, tool
from julep.execution.llm import make_local_reasoner
from julep.execution.llm_result import LlmCallMeta, LlmResult
from julep.registry import DEFAULT_REGISTRY
from conftest import run

if HAVE_TEMPORAL:
    from julep.execution import harness
    from julep.execution.harness import AgentInput, AgentWorkflow


@dataclass
class FakePromptTokensDetails:
    cached_tokens: int | None = None


@dataclass
class FakeUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    prompt_tokens_details: FakePromptTokensDetails | None = None


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
    usage: FakeUsage | None = None
    model: str | None = None


def _completion(content: Any, usage: FakeUsage | None = None) -> FakeCompletion:
    return FakeCompletion(
        choices=[FakeChoice(FakeMessage(content=json.dumps(content)))],
        usage=usage,
        model="claude-test",
    )


@dataclass
class Recorder:
    replies: list[FakeCompletion]
    calls: list[dict[str, Any]] = field(default_factory=list)
    _i: int = 0

    async def __call__(self, **kwargs: Any) -> FakeCompletion:
        self.calls.append(kwargs)
        reply = self.replies[self._i]
        self._i += 1
        return reply


def _controller_reasoner(
    suffix: str,
    *,
    prompt_cache: str | None = "1h",
    reasoning_effort: str | None = "high",
    temperature: float | None = 0.2,
    max_tokens: int | None = 512,
) -> Reasoner:
    return Reasoner(
        name=f"provider_fields_source_{suffix}",
        model="anthropic:claude-x",
        system="stable controller prompt",
        prompt_cache=prompt_cache,
        reasoning_effort=reasoning_effort,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _provider_fields(reasoner: Reasoner) -> tuple[Any, ...]:
    return (
        reasoner.prompt_cache,
        reasoner.reasoning_effort,
        reasoner.temperature,
        reasoner.max_tokens,
    )


def test_agent_facade_captures_reasoner_provider_fields_into_registry() -> None:
    agent = Agent(_controller_reasoner("capture"))

    registered = get_reasoner(agent.name)

    assert registered.prompt_cache == "1h"
    assert registered.reasoning_effort == "high"
    assert registered.temperature == 0.2
    assert registered.max_tokens == 512


def test_agent_facade_plain_model_has_no_prompt_cache() -> None:
    agent = Agent("anthropic:claude-x", name="provider_fields_plain_model")

    registered = get_reasoner(agent.name)

    assert registered.prompt_cache is None
    assert registered.reasoning_effort is None
    assert registered.temperature is None
    assert registered.max_tokens is None


@pytest.mark.parametrize(
    ("field", "first", "second"),
    [
        ("prompt_cache", "1h", "5m"),
        ("reasoning_effort", "high", "low"),
        ("temperature", 0.1, 0.9),
        ("max_tokens", 256, 1024),
    ],
)
def test_default_agent_names_include_set_provider_fields(
    field: str,
    first: Any,
    second: Any,
) -> None:
    base = {
        "prompt_cache": None,
        "reasoning_effort": None,
        "temperature": None,
        "max_tokens": None,
    }
    first_kwargs = {**base, field: first}
    second_kwargs = {**base, field: second}

    first_agent = Agent(_controller_reasoner(f"name_{field}_first", **first_kwargs))
    second_agent = Agent(_controller_reasoner(f"name_{field}_second", **second_kwargs))

    assert first_agent.name != second_agent.name


def test_derived_agents_preserve_controller_provider_fields() -> None:
    @tool(effect="read", idempotent=True)
    def provider_fields_lookup(value: str) -> str:
        return value

    @tool(effect="read", idempotent=True)
    def provider_fields_extra(value: str) -> str:
        return value

    agent = Agent(
        _controller_reasoner("derived"),
        tools=[provider_fields_lookup],
    )
    expected = ("1h", "high", 0.2, 512)

    derived = [
        agent.with_tools(add=[provider_fields_extra]),
        agent.without(provider_fields_lookup),
        agent.replace(max_rounds=3),
    ]

    for derived_agent in derived:
        assert _provider_fields(get_reasoner(derived_agent.name)) == expected


def test_replace_reasoner_captures_new_provider_fields() -> None:
    agent = Agent(_controller_reasoner("replace_old", prompt_cache="5m"))

    replaced = agent.replace(
        reasoner=_controller_reasoner(
            "replace_new",
            prompt_cache="1h",
            reasoning_effort="low",
            temperature=0.7,
            max_tokens=1024,
        )
    )

    registered = get_reasoner(replaced.name)
    assert registered.prompt_cache == "1h"
    assert registered.reasoning_effort == "low"
    assert registered.temperature == 0.7
    assert registered.max_tokens == 1024


def test_local_agent_loop_applies_prompt_cache_and_surfaces_meta() -> None:
    rec = Recorder(
        [
            _completion(
                {"output": "done"},
                usage=FakeUsage(
                    prompt_tokens=10,
                    completion_tokens=2,
                    total_tokens=12,
                    prompt_tokens_details=FakePromptTokensDetails(cached_tokens=7),
                ),
            )
        ]
    )
    agent = Agent(
        Reasoner(
            name="provider_fields_local_source",
            model="anthropic:claude-x",
            system="stable controller prompt",
            prompt_cache="1h",
        ),
        name="provider_fields_local_agent",
        llm=make_local_reasoner(acompletion=rec),
    )

    result = agent.run({"task": "go"})

    sent = rec.calls[0]["messages"]
    system = next(message for message in sent if message["role"] == "system")
    assert system["content"][0]["cache_control"] == {
        "type": "ephemeral",
        "ttl": "1h",
    }
    assert result["status"] == "done"
    assert result["output"] == "done"
    assert result["__ca_meta__"]["llm.cache"] == {
        "requested": "1h",
        "applied": True,
        "read": 7,
    }


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_agent_workflow_resolves_controller_reasoner_from_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = Agent(
        Reasoner(
            name="provider_fields_temporal_source",
            model="anthropic:claude-x",
            system="stable controller prompt",
            prompt_cache="1h",
        )
    )
    payloads: list[Any] = []

    async def fake_execute_activity(fn: Any, payload: Any, **kwargs: Any) -> Any:
        del kwargs
        payloads.append(payload)
        if fn.__name__ == "invokeReasoner":
            registered = DEFAULT_REGISTRY.get_reasoner(payload.reasoner)
            assert registered.prompt_cache == "1h"
            return {
                "reply": {"output": "done"},
                "__ca_meta__": {"llm.cache": {"requested": "1h", "applied": True}},
            }
        return None

    monkeypatch.setattr(harness.workflow, "execute_activity", fake_execute_activity)
    out = asyncio.run(
        AgentWorkflow().run(
            AgentInput(
                controller=agent.name,
                session_id="provider-fields-temporal",
                input={"task": "go"},
                config=agent._cfg.to_json(),
                resolve_spec=False,
            )
        )
    )

    assert out["status"] == "done"
    assert out["__ca_meta__"]["llm.cache"]["requested"] == "1h"
    reasoner_payloads = [
        payload
        for payload in payloads
        if isinstance(payload, harness.InvokeReasonerInput)
    ]
    assert len(reasoner_payloads) == 1
    assert reasoner_payloads[0].reasoner == agent.name


def test_agent_deploy_identity_changes_with_prompt_cache_and_unset_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The artifact hash embeds frameworkVersion, so a raw golden breaks on
    # every release (and on stale local .venv metadata). Pin the version so
    # the golden guards the OTHER identity inputs against unintended drift.
    # (import_module: the package's `deploy` FUNCTION shadows the submodule.)
    deploy_mod = importlib.import_module("julep.deploy")

    monkeypatch.setattr(
        deploy_mod, "_framework_version", lambda: "pinned-for-identity-golden"
    )
    unset = Agent(
        "anthropic:claude-x",
        name="agent_provider_fields_identity_unset",
        instructions="stable system",
    )
    cached = Agent(
        Reasoner(
            name="provider_fields_identity_source",
            model="anthropic:claude-x",
            system="stable system",
            prompt_cache="1h",
        ),
        name="agent_provider_fields_identity_cached",
    )

    assert unset.deployment().artifact_hash == (
        "sha256:fad89f6f97f80b718d89d613122526c905a196568b763c37aa56d54e9a9e1284"
    )
    assert cached.deployment().artifact_hash != unset.deployment().artifact_hash


def test_cma_rejects_prompt_cache_on_controller_reasoner() -> None:
    from cma_fakes import FakeCMAClient, FakeCMASession

    agent = Agent(
        Reasoner(
            name="provider_fields_cma_source",
            model="anthropic:claude-x",
            system="stable controller prompt",
            prompt_cache="1h",
        ),
        name="provider_fields_cma_agent",
    )
    client = FakeCMAClient(FakeCMASession([]))

    with pytest.raises(ValueError, match="prompt_cache.*CMA.*vendor runs the loop"):
        agent.run_on_cma({"task": "go"}, client=client)


def test_cma_loop_rejects_prompt_cache_on_registry_reasoner() -> None:
    from julep.agent_loop import AgentConfig
    from julep.execution.cma import CMAEvent, drive_cma_agent_loop
    from cma_fakes import FakeCMASession

    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(
            name="provider_fields_cma_loop_agent",
            model="anthropic:claude-x",
            prompt_cache="1h",
        )
    )
    session = FakeCMASession([CMAEvent("terminal", output="done")])

    async def call_tool(_tool: str, _value: Any, _cid: str) -> Any:
        raise AssertionError("no tools should be called")

    with pytest.raises(ValueError, match="prompt_cache.*CMA.*vendor runs the loop"):
        run(
            drive_cma_agent_loop(
                input={"task": "go"},
                cfg=AgentConfig(),
                session=session,
                call_tool=call_tool,
                controller="provider_fields_cma_loop_agent",
                session_cid="provider_fields_cma_loop_agent",
            )
        )


def test_lint_keeps_llm_result_import_exercised() -> None:
    meta = LlmCallMeta(
        served_model="claude-test",
        provider="anthropic",
        prompt_cache_requested="1h",
        prompt_cache_applied=True,
    )
    assert LlmResult(reply={"output": "ok"}, meta=meta).meta.to_attrs()["llm.cache"]
