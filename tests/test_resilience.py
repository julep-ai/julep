"""Pure-core provider resilience: error taxonomy, fallback policy, breaker."""

from __future__ import annotations

import pytest

from composable_agents.errors import ResilienceExhausted
from composable_agents.resilience import (
    AttemptRecord,
    CircuitBreaker,
    ErrorClass,
    ResiliencePolicy,
    classify_error,
    summarize_attempts,
)


class HttpError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class WrappedHttpError(Exception):
    """SDK style: the status rides on an attached response object."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)

        class _Resp:
            pass

        resp = _Resp()
        resp.status_code = status_code
        self.response = resp


# --------------------------------------------------------------------------- #
# classify_error
# --------------------------------------------------------------------------- #
def test_timeout_types_win() -> None:
    assert classify_error(TimeoutError("deadline")) is ErrorClass.TIMEOUT


@pytest.mark.parametrize("status", [408, 429, 500, 502, 503, 504, 520, 529])
def test_transient_statuses(status: int) -> None:
    assert classify_error(HttpError("boom", status)) is ErrorClass.TRANSIENT


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_config_statuses(status: int) -> None:
    assert classify_error(HttpError("boom", status)) is ErrorClass.CONFIG


def test_status_found_on_response_attribute() -> None:
    assert classify_error(WrappedHttpError("boom", 503)) is ErrorClass.TRANSIENT


def test_message_hints_without_status() -> None:
    assert classify_error(Exception("Invalid API key provided")) is ErrorClass.CONFIG
    assert classify_error(Exception("model not found: gpt-99")) is ErrorClass.CONFIG
    assert classify_error(Exception("request timed out after 60s")) is ErrorClass.TIMEOUT


def test_unknown_errors_default_transient() -> None:
    assert classify_error(Exception("the provider sneezed")) is ErrorClass.TRANSIENT


def test_auth_error_in_chain_wins_over_transient_top() -> None:
    # A reissued call's transient failure must not mask the original 401.
    try:
        try:
            raise HttpError("invalid api key", 401)
        except HttpError:
            raise HttpError("overloaded", 503) from None  # implicit __context__ kept
    except HttpError as exc:
        chained = exc
    assert classify_error(chained) is ErrorClass.CONFIG


def test_non_auth_config_in_chain_does_not_propagate() -> None:
    # A 422 native failure (e.g. response_format unsupported) is ambiguous:
    # the top error still decides, so a transient reissue failure stays transient.
    try:
        try:
            raise HttpError("response_format unsupported", 422)
        except HttpError:
            raise HttpError("overloaded", 503) from None
    except HttpError as exc:
        chained = exc
    assert classify_error(chained) is ErrorClass.TRANSIENT


def test_chain_walk_survives_cycles() -> None:
    a = Exception("a")
    b = Exception("b")
    a.__context__ = b
    b.__context__ = a
    assert classify_error(a) is ErrorClass.TRANSIENT


# --------------------------------------------------------------------------- #
# ResiliencePolicy
# --------------------------------------------------------------------------- #
def test_candidates_chain_in_order_deduplicated() -> None:
    policy = ResiliencePolicy(
        fallbacks={"openai:gpt-a": ("anthropic:claude-b", "openai:gpt-a", "groq:c")}
    )
    assert policy.candidates("openai:gpt-a") == (
        "openai:gpt-a", "anthropic:claude-b", "groq:c",
    )


def test_candidates_without_chain_is_just_the_model() -> None:
    assert ResiliencePolicy().candidates("solo") == ("solo",)


def test_attempts_per_error_class() -> None:
    policy = ResiliencePolicy(transient_attempts=3, timeout_attempts=2)
    assert policy.attempts_for(ErrorClass.TRANSIENT) == 3
    assert policy.attempts_for(ErrorClass.TIMEOUT) == 2
    assert policy.attempts_for(ErrorClass.MODEL_BEHAVIOR) == 1
    assert policy.attempts_for(ErrorClass.CONFIG) == 1
    # Never below one attempt, even when misconfigured.
    assert ResiliencePolicy(transient_attempts=0).attempts_for(ErrorClass.TRANSIENT) == 1


def test_backoff_curve_is_capped() -> None:
    policy = ResiliencePolicy(initial_backoff_s=1.0, backoff_factor=2.0, max_backoff_s=3.0)
    assert policy.backoff_s(0) == 1.0
    assert policy.backoff_s(1) == 2.0
    assert policy.backoff_s(2) == 3.0  # capped
    assert policy.backoff_s(10) == 3.0


# --------------------------------------------------------------------------- #
# CircuitBreaker
# --------------------------------------------------------------------------- #
class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_breaker_opens_after_threshold_and_recovers() -> None:
    clock = Clock()
    breaker = CircuitBreaker(failure_threshold=2, cooldown_s=10.0, clock=clock)

    assert breaker.allow("openai")
    breaker.record_failure("openai")
    assert breaker.allow("openai")          # one failure: still closed
    breaker.record_failure("openai")
    assert not breaker.allow("openai")      # threshold reached: open
    assert breaker.state("openai") == "open"

    clock.now = 10.0
    assert breaker.allow("openai")          # cooldown elapsed: half-open probe
    assert breaker.state("openai") == "half_open"

    breaker.record_failure("openai")        # probe failed: cooldown re-armed
    assert not breaker.allow("openai")
    clock.now = 19.9
    assert not breaker.allow("openai")
    clock.now = 20.0
    assert breaker.allow("openai")

    breaker.record_success("openai")        # probe succeeded: fully closed
    assert breaker.state("openai") == "closed"
    breaker.record_failure("openai")
    assert breaker.allow("openai")          # count restarted from zero


def test_breaker_keys_are_independent() -> None:
    breaker = CircuitBreaker(failure_threshold=1, cooldown_s=60.0, clock=Clock())
    breaker.record_failure("openai")
    assert not breaker.allow("openai")
    assert breaker.allow("anthropic")


def test_breaker_rejects_bad_threshold() -> None:
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=0)


# --------------------------------------------------------------------------- #
# Attempt records + exhaustion error
# --------------------------------------------------------------------------- #
def test_summarize_attempts_one_line() -> None:
    attempts = [
        AttemptRecord(model="a", provider="p", outcome="transient", detail="503"),
        AttemptRecord(model="b", provider="q", outcome="ok"),
    ]
    assert summarize_attempts(attempts) == "a:transient (503) -> b:ok"


def test_resilience_exhausted_carries_attempts() -> None:
    attempts = [AttemptRecord(model="a", provider="p", outcome="transient", detail="503")]
    err = ResilienceExhausted(attempts)
    assert err.attempts == attempts
    assert "a:transient" in str(err)


# --------------------------------------------------------------------------- #
# ExecutionPolicy knob
# --------------------------------------------------------------------------- #
def test_execution_policy_roundtrips_brain_max_attempts() -> None:
    from composable_agents.execution.policy import ExecutionPolicy

    policy = ExecutionPolicy(brain_max_attempts=1)
    assert ExecutionPolicy.from_json(policy.to_json()).brain_max_attempts == 1
    assert ExecutionPolicy.from_json({}).brain_max_attempts == 4
