"""Opt-in smoke tests for real model providers through the Julep agent loop.

These tests make billable network calls and are excluded from the default test
run by the ``live`` marker. Load provider credentials before selecting them::

    set -a; source .env; set +a
    uv run --extra provider-smoke python -m pytest \
        -m provider_smoke tests/test_provider_agent_smoke.py

Every case runs the same tool-using Julep Agent. A passing test proves that the
provider can drive a tool round, receive the tool result, and finish the agent
run. Override a default model with the ``JULEP_SMOKE_*_MODEL`` environment
variable shown in ``CASES`` when a provider retires or restricts a model.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

import pytest

from julep import Agent, tool
from julep.execution.llm import make_local_reasoner
from julep.execution.openai_responses import uses_openai_responses

SMOKE_LABEL = "provider-smoke"
SMOKE_TOKEN = "julep-provider-smoke-ok"


@dataclass(frozen=True)
class ProviderCase:
    id: str
    model: str
    model_env: str
    credential_envs: tuple[str, ...]
    reasoning_effort: Optional[str] = None

    @property
    def resolved_model(self) -> str:
        return os.environ.get(self.model_env, self.model)

    @property
    def has_credentials(self) -> bool:
        return any(os.environ.get(name) for name in self.credential_envs)


CASES = (
    ProviderCase(
        id="google-gemini",
        model="gemini:gemini-2.5-flash",
        model_env="JULEP_SMOKE_GEMINI_MODEL",
        credential_envs=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    ),
    ProviderCase(
        id="openai-chat-completions",
        model="openai:gpt-4o-mini",
        model_env="JULEP_SMOKE_OPENAI_CHAT_MODEL",
        credential_envs=("OPENAI_API_KEY",),
    ),
    ProviderCase(
        id="openai-responses",
        model="openai:gpt-5.6-sol",
        model_env="JULEP_SMOKE_OPENAI_RESPONSES_MODEL",
        credential_envs=("OPENAI_API_KEY",),
        reasoning_effort="low",
    ),
    ProviderCase(
        id="anthropic",
        model="anthropic:claude-haiku-4-5-20251001",
        model_env="JULEP_SMOKE_ANTHROPIC_MODEL",
        credential_envs=("ANTHROPIC_API_KEY",),
    ),
    ProviderCase(
        id="openrouter",
        model="openrouter:openai/gpt-4o-mini",
        model_env="JULEP_SMOKE_OPENROUTER_MODEL",
        credential_envs=("OPENROUTER_API_KEY",),
    ),
    ProviderCase(
        id="xai",
        model="xai:grok-4.20-non-reasoning-latest",
        model_env="JULEP_SMOKE_XAI_MODEL",
        credential_envs=("XAI_API_KEY",),
    ),
)


@tool(effect="read", idempotent=True, name="provider_smoke_lookup")
def provider_smoke_lookup(label: str, nonce: str = "") -> dict[str, str]:
    """Return the fixed smoke token for a requested label."""
    del nonce
    return {"label": label, "token": SMOKE_TOKEN}


def _build_agent(case: ProviderCase) -> Agent:
    first_action = json.dumps(
        {"tool": "provider_smoke_lookup", "input": {"label": SMOKE_LABEL}},
        sort_keys=True,
    )
    second_action = json.dumps(
        {"output": {"label": SMOKE_LABEL, "token": SMOKE_TOKEN}},
        sort_keys=True,
    )
    return Agent(
        case.resolved_model,
        tools=[provider_smoke_lookup],
        name=f"provider_smoke_{case.id.replace('-', '_')}",
        instructions=(
            "Each turn receives an object with 'input' and 'trace'. Follow this "
            "procedure exactly: (1) If trace is empty, reply with "
            f"{first_action}. (2) If trace is not empty, do not call any tool; "
            f"the input is the tool result, so reply with {second_action}. "
            "Always use valid JSON with double quotes and no markdown. The "
            "second rule always overrides the first."
        ),
        reasoning_effort=case.reasoning_effort,
        max_tokens=256,
        max_rounds=3,
        llm=make_local_reasoner(),
    )


@pytest.mark.live
@pytest.mark.provider_smoke
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_real_provider_can_drive_julep_agent(case: ProviderCase) -> None:
    if not case.has_credentials:
        pytest.skip(f"one of {case.credential_envs!r} is required")

    provider, separator, model = case.resolved_model.partition(":")
    if case.id == "openai-chat-completions":
        assert separator and not uses_openai_responses(provider, model)
    elif case.id == "openai-responses":
        assert separator and uses_openai_responses(provider, model)

    result = _build_agent(case).run("Run the provider smoke check now.")

    assert result.status == "done"
    assert [entry["decision"] for entry in result.trace] == ["call"]
    assert SMOKE_LABEL in json.dumps(result.output, sort_keys=True)
    assert SMOKE_TOKEN in json.dumps(result.output, sort_keys=True)
