"""The resilient LlmCaller: deterministic fallback walking around complete_reasoner.

No network, no any-llm: a scripted ``acompletion`` raises or replies on cue, a
recording ``sleep`` replaces real backoff, and a fake clock drives the breaker.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from julep.dotctx import Reasoner
from julep.errors import ResilienceExhausted
from julep.execution.llm import make_resilient_llm_caller
from julep.resilience import AttemptRecord, CircuitBreaker, ResiliencePolicy
from conftest import run


# --------------------------------------------------------------------------- #
# Fakes. Completion shapes are shared with tests/test_llm.py; Script differs
# from its Recorder in that a scripted step may RAISE (the point of this file).
# --------------------------------------------------------------------------- #
from test_llm import FakeChoice, FakeCompletion, FakeMessage


def _reply(content: Any) -> FakeCompletion:
    return FakeCompletion(choices=[FakeChoice(FakeMessage(content=content))])


class HttpError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class Script:
    """An ``acompletion`` that replays steps: an Exception raises, else returns."""

    steps: list[Any]
    calls: list[dict[str, Any]] = field(default_factory=list)
    _i: int = 0

    async def __call__(self, **kwargs: Any) -> FakeCompletion:
        self.calls.append(kwargs)
        step = self.steps[self._i]
        self._i += 1
        if isinstance(step, Exception):
            raise step
        assert isinstance(step, FakeCompletion)
        return step


def _caller(script: Script, policy: ResiliencePolicy, **kwargs: Any):
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    attempts: list[AttemptRecord] = []
    caller = make_resilient_llm_caller(
        policy=policy,
        acompletion=script,
        sleep=fake_sleep,
        on_attempt=attempts.append,
        **kwargs,
    )
    return caller, attempts, sleeps


_CHAIN = {"openai:gpt-a": ("anthropic:claude-b",)}


def _reasoner(**kwargs: Any) -> Reasoner:
    return Reasoner(name="t", model="openai:gpt-a", system="sys", **kwargs)


# --------------------------------------------------------------------------- #
# Behavior
# --------------------------------------------------------------------------- #
def test_primary_success_walks_nothing() -> None:
    script = Script([_reply("fine")])
    caller, attempts, sleeps = _caller(script, ResiliencePolicy(fallbacks=_CHAIN))

    assert run(caller(_reasoner(), "hi")).reply == "fine"
    assert [a.outcome for a in attempts] == ["ok"]
    assert attempts[0].model == "openai:gpt-a"
    assert sleeps == []
    assert len(script.calls) == 1


def test_transient_retries_then_falls_back() -> None:
    script = Script([
        HttpError("overloaded", 503),
        HttpError("overloaded", 503),
        _reply("rescued"),
    ])
    policy = ResiliencePolicy(fallbacks=_CHAIN, transient_attempts=2, initial_backoff_s=0.25)
    caller, attempts, sleeps = _caller(script, policy)

    assert run(caller(_reasoner(), "hi")).reply == "rescued"
    assert [(a.model, a.outcome) for a in attempts] == [
        ("openai:gpt-a", "transient"),
        ("openai:gpt-a", "transient"),
        ("anthropic:claude-b", "ok"),
    ]
    assert sleeps == [0.25]  # one backoff between the two same-model attempts


def test_timeout_advances_after_single_attempt() -> None:
    script = Script([TimeoutError("deadline"), _reply("rescued")])
    policy = ResiliencePolicy(fallbacks=_CHAIN, timeout_attempts=1)
    caller, attempts, sleeps = _caller(script, policy)

    assert run(caller(_reasoner(), "hi")).reply == "rescued"
    assert [a.outcome for a in attempts] == ["timeout", "ok"]
    assert sleeps == []


def test_config_error_fails_fast_never_falls_back() -> None:
    script = Script([HttpError("invalid api key", 401)])
    caller, attempts, _ = _caller(script, ResiliencePolicy(fallbacks=_CHAIN))

    with pytest.raises(HttpError, match="invalid api key"):
        run(caller(_reasoner(), "hi"))
    assert [a.outcome for a in attempts] == ["config"]
    assert len(script.calls) == 1  # the fallback model was never consulted


def test_exhausted_chain_raises_with_full_attempt_log() -> None:
    script = Script([HttpError("down", 503), HttpError("also down", 502)])
    policy = ResiliencePolicy(fallbacks=_CHAIN, transient_attempts=1)
    caller, attempts, _ = _caller(script, policy)

    with pytest.raises(ResilienceExhausted) as excinfo:
        run(caller(_reasoner(), "hi"))
    assert [a.model for a in excinfo.value.attempts] == ["openai:gpt-a", "anthropic:claude-b"]
    assert isinstance(excinfo.value.__cause__, HttpError)
    assert attempts == excinfo.value.attempts


def test_open_circuit_skips_provider_deterministically() -> None:
    breaker = CircuitBreaker(failure_threshold=1, cooldown_s=60.0, clock=lambda: 0.0)
    breaker.record_failure("openai")  # circuit for openai is now open

    script = Script([_reply("rescued")])
    policy = ResiliencePolicy(fallbacks=_CHAIN, transient_attempts=1)
    caller, attempts, _ = _caller(script, policy, breaker=breaker)

    assert run(caller(_reasoner(), "hi")).reply == "rescued"
    assert [(a.provider, a.outcome) for a in attempts] == [
        ("openai", "skipped_open_circuit"),
        ("anthropic", "ok"),
    ]
    assert len(script.calls) == 1
    assert breaker.state("anthropic") == "closed"


def test_circuit_opened_mid_candidate_stops_same_model_retries() -> None:
    # threshold=1: the first failure opens the circuit; the remaining
    # same-model retry budget must not keep hammering the provider.
    breaker = CircuitBreaker(failure_threshold=1, cooldown_s=60.0, clock=lambda: 0.0)
    script = Script([HttpError("down", 503), _reply("rescued")])
    policy = ResiliencePolicy(fallbacks=_CHAIN, transient_attempts=3)
    caller, attempts, sleeps = _caller(script, policy, breaker=breaker)

    assert run(caller(_reasoner(), "hi")).reply == "rescued"
    assert [(a.model, a.outcome) for a in attempts] == [
        ("openai:gpt-a", "transient"),
        ("anthropic:claude-b", "ok"),
    ]
    assert sleeps == []                # no backoff: we advanced, not retried
    assert len(script.calls) == 2      # exactly one call to the opened provider


def test_failures_charge_the_breaker() -> None:
    breaker = CircuitBreaker(failure_threshold=2, cooldown_s=60.0, clock=lambda: 0.0)
    script = Script([HttpError("down", 503), HttpError("down", 503), _reply("rescued")])
    policy = ResiliencePolicy(fallbacks=_CHAIN, transient_attempts=2)
    caller, _, _ = _caller(script, policy, breaker=breaker)

    assert run(caller(_reasoner(), "hi")).reply == "rescued"
    assert breaker.state("openai") == "open"      # two transient failures
    assert breaker.state("anthropic") == "closed"


def test_auth_error_fails_fast_without_prompt_injected_reissue() -> None:
    # complete_reasoner classifies a failed native structured call before
    # reissuing: a CONFIG-class error (bad key) re-raises immediately, so the
    # prompt-injected fallback never runs and can never mask it.
    schema = {"type": "object"}
    script = Script([HttpError("invalid api key", 401), HttpError("overloaded", 503)])
    caller, attempts, _ = _caller(script, ResiliencePolicy(fallbacks=_CHAIN))

    with pytest.raises(HttpError, match="invalid api key"):
        run(caller(_reasoner(reply=schema), "hi"))
    assert [a.outcome for a in attempts] == ["config"]
    assert len(script.calls) == 1  # native only; no injected reissue, no fallback model


def test_custom_classifier_overrides_default() -> None:
    from julep.resilience import ErrorClass

    script = Script([RuntimeError("sdk-wrapped quota error"), _reply("rescued")])
    policy = ResiliencePolicy(fallbacks=_CHAIN, timeout_attempts=1)
    caller, attempts, sleeps = _caller(
        script, policy, classifier=lambda exc: ErrorClass.TIMEOUT
    )

    assert run(caller(_reasoner(), "hi")).reply == "rescued"
    assert [a.outcome for a in attempts] == ["timeout", "ok"]
    assert sleeps == []


def test_model_behavior_advances_without_charging_breaker() -> None:
    schema = {"type": "object", "properties": {"queue": {"type": "string"}}}
    breaker = CircuitBreaker(failure_threshold=1, cooldown_s=60.0, clock=lambda: 0.0)
    script = Script([
        _reply("not json at all"),                  # provider fine, model misbehaved
        _reply(json.dumps({"queue": "billing"})),
    ])
    caller, attempts, _ = _caller(script, ResiliencePolicy(fallbacks=_CHAIN), breaker=breaker)

    assert run(caller(_reasoner(reply=schema), "hi")).reply == {"queue": "billing"}
    assert [a.outcome for a in attempts] == ["model_behavior", "ok"]
    assert breaker.state("openai") == "closed"      # answered: not an outage
