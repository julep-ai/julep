"""Provider resilience: deterministic fallback policy + circuit breaker (pure core).

LLM providers fail often enough that "retry the same model harder" is not a
strategy. This module owns the *policy* side of surviving that: an error
taxonomy (:func:`classify_error`), a declarative, deterministic fallback chain
(:class:`ResiliencePolicy`), and a per-provider :class:`CircuitBreaker`. The
*mechanism* — actually walking the chain around a model call — lives in
:func:`composable_agents.execution.llm.make_resilient_llm_caller`, the worker's
``LlmCaller`` seam.

Determinism here means deterministic **policy**, not replay-identical results:
the same error class on the same model always produces the same next decision
(retry, advance to the same next model, or fail fast). Which provider happened
to be up when a run executed is recorded per attempt (:class:`AttemptRecord`),
never re-derived on replay. Breaker state is process-local worker state — it
belongs in activities/steps, which are allowed to be nondeterministic; never
consult it from workflow code.

Fail-fast contract: a :data:`ErrorClass.CONFIG` error (bad API key, unknown
model, malformed request) is never masked by a fallback — it re-raises
immediately so misconfiguration stays loud.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Optional, Sequence


class ErrorClass(Enum):
    """What a model-call failure means for the next decision."""

    TRANSIENT = "transient"            # provider hiccup: retry, then fall back
    TIMEOUT = "timeout"                # took too long: one more try, then fall back
    CONFIG = "config"                  # our mistake: fail fast, never fall back
    MODEL_BEHAVIOR = "model_behavior"  # bad reply shape: next model, provider unharmed


# HTTP status codes that indicate a retryable provider-side condition.
TRANSIENT_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504, 520, 529})
# HTTP status codes that indicate a request/configuration problem on our side.
CONFIG_STATUS = frozenset({400, 401, 403, 404, 422})
# The unambiguous subset of CONFIG: an auth failure anywhere in an exception
# chain means misconfiguration even when a later attempt failed differently.
AUTH_STATUS = frozenset({401, 403})

_CONFIG_HINTS = (
    "api key",
    "api_key",
    "authentication",
    "unauthorized",
    "permission",
    "model not found",
    "no such model",
    "invalid request",
)
_AUTH_HINTS = ("api key", "api_key", "authentication", "unauthorized", "permission")
_TIMEOUT_HINTS = ("timed out", "timeout")


def _status_of(exc: BaseException) -> Optional[int]:
    """Best-effort HTTP status from the provider SDK exception zoo."""
    for attr in ("status_code", "http_status", "status", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        value = getattr(response, "status_code", None)
        if isinstance(value, int):
            return value
    return None


def _is_auth_error(exc: BaseException) -> bool:
    status = _status_of(exc)
    if status in AUTH_STATUS:
        return True
    message = str(exc).lower()
    return any(hint in message for hint in _AUTH_HINTS)


def is_auth_error(exc: BaseException) -> bool:
    """True when an auth failure sits anywhere in ``exc``'s cause/context chain.

    The unambiguous subset of CONFIG: a bad key or missing permission is
    misconfiguration no matter what a later retry died of. Callers use this
    where the broader CONFIG class (400/404/422 bad requests) must still be
    allowed to try a differently-shaped request.
    """
    return any(_is_auth_error(link) for link in _chain(exc))


def _chain(exc: BaseException) -> list[BaseException]:
    """``exc`` plus its full ``__cause__``/``__context__`` ancestry (cycle-safe).

    Both links are followed: ``raise X from Y`` inside an ``except Z:`` block
    leaves ``__cause__ = Y`` *and* ``__context__ = Z`` populated, and an auth
    error hiding in either branch must be found.
    """
    out: list[BaseException] = []
    seen: set[int] = set()
    stack: list[Optional[BaseException]] = [exc]
    while stack:
        current = stack.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        out.append(current)
        stack.append(current.__cause__)
        stack.append(current.__context__)
    return out


def classify_error(exc: BaseException) -> ErrorClass:
    """Map a model-call exception to its :class:`ErrorClass`.

    An auth error anywhere in the ``__cause__``/``__context__`` chain wins:
    callers like ``complete_reasoner`` reissue a failed native structured call
    with a prompt-injected schema, and the reissue's failure (often transient)
    would otherwise mask the original 401/403 — a bad key must stay CONFIG no
    matter what the second attempt died of. For the rest, the *top* exception
    decides: explicit timeout types, then HTTP status, then message hints. The
    default is TRANSIENT — an unrecognized provider error should be survivable,
    while genuinely settled errors are expected to carry a status or hint.
    """
    if any(_is_auth_error(link) for link in _chain(exc)):
        return ErrorClass.CONFIG

    if isinstance(exc, TimeoutError):
        return ErrorClass.TIMEOUT

    status = _status_of(exc)
    if status is not None:
        if status in CONFIG_STATUS:
            return ErrorClass.CONFIG
        if status in TRANSIENT_STATUS:
            return ErrorClass.TRANSIENT

    message = str(exc).lower()
    if any(hint in message for hint in _CONFIG_HINTS):
        return ErrorClass.CONFIG
    if any(hint in message for hint in _TIMEOUT_HINTS):
        return ErrorClass.TIMEOUT
    return ErrorClass.TRANSIENT


@dataclass(frozen=True)
class AttemptRecord:
    """One model-call attempt, for trace attribution and observability sinks."""

    model: str
    provider: str
    outcome: str  # "ok", "skipped_open_circuit", or an ErrorClass value
    detail: str = ""
    tier: Optional[str] = None
    batch_id: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.outcome == "ok"


OnAttempt = Callable[[AttemptRecord], None]


@dataclass(frozen=True)
class ResiliencePolicy:
    """A deterministic fallback plan for model calls.

    ``fallbacks`` maps a primary model slug to its ranked fallback models
    (each entry uses the same ``"provider:model"`` addressing as
    :class:`~composable_agents.dotctx.Reasoner`). The chain is walked strictly in
    order; there is no load balancing and no randomness. Per-class same-model
    attempt counts and the backoff curve are the only other knobs.
    """

    fallbacks: Mapping[str, Sequence[str]] = field(default_factory=dict)
    transient_attempts: int = 2
    timeout_attempts: int = 1
    initial_backoff_s: float = 0.5
    backoff_factor: float = 2.0
    max_backoff_s: float = 8.0

    def candidates(self, model: str) -> tuple[str, ...]:
        """The primary model followed by its fallbacks, deduplicated in order."""
        out: list[str] = []
        for candidate in (model, *self.fallbacks.get(model, ())):
            if candidate not in out:
                out.append(candidate)
        return tuple(out)

    def attempts_for(self, error_class: ErrorClass) -> int:
        """Same-model attempt budget for an error class (>= 1)."""
        if error_class is ErrorClass.TRANSIENT:
            return max(1, self.transient_attempts)
        if error_class is ErrorClass.TIMEOUT:
            return max(1, self.timeout_attempts)
        return 1  # CONFIG fails fast; MODEL_BEHAVIOR advances to the next model

    def backoff_s(self, retry_index: int) -> float:
        """Backoff before same-model retry ``retry_index`` (0-based)."""
        return min(
            self.initial_backoff_s * (self.backoff_factor ** retry_index),
            self.max_backoff_s,
        )


class CircuitBreaker:
    """Per-key (provider) breaker: closed -> open after N consecutive failures,
    half-open after a cooldown (one probe through; failure re-arms the cooldown).

    ``allow`` *consumes* the half-open probe: the first caller after the
    cooldown re-arms the window, so concurrent callers on the same event loop
    stay blocked until that probe settles (success closes, failure re-arms).
    ``state`` is a pure read and never consumes the probe.

    Process-local worker state with an injectable monotonic clock. Thread-safety
    is not provided; use one breaker per event loop / worker process.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        cooldown_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        self._threshold = failure_threshold
        self._cooldown_s = cooldown_s
        self._clock = clock
        self._failures: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}

    def _cooldown_elapsed(self, key: str) -> Optional[bool]:
        """None when closed; else whether the open window's cooldown has passed."""
        opened_at = self._opened_at.get(key)
        if opened_at is None:
            return None
        return (self._clock() - opened_at) >= self._cooldown_s

    def allow(self, key: str) -> bool:
        """True when a call to ``key`` may proceed (closed, or half-open probe).

        Consuming: when the cooldown has elapsed, the caller is granted the
        single half-open probe and the window is re-armed so other callers are
        blocked until this probe records a success or failure.
        """
        elapsed = self._cooldown_elapsed(key)
        if elapsed is None:
            return True
        if elapsed:
            self._opened_at[key] = self._clock()
            return True
        return False

    def record_success(self, key: str) -> None:
        self._failures.pop(key, None)
        self._opened_at.pop(key, None)

    def record_failure(self, key: str) -> None:
        count = self._failures.get(key, 0) + 1
        self._failures[key] = count
        if count >= self._threshold:
            # Open (or re-arm a half-open probe's cooldown).
            self._opened_at[key] = self._clock()

    def state(self, key: str) -> str:
        """``"closed"``, ``"open"``, or ``"half_open"`` — a pure read for
        dashboards/tests; never consumes the half-open probe."""
        elapsed = self._cooldown_elapsed(key)
        if elapsed is None:
            return "closed"
        return "half_open" if elapsed else "open"


def summarize_attempts(attempts: Sequence[AttemptRecord]) -> str:
    """A one-line, log-friendly account of a resilience walk."""
    return " -> ".join(
        f"{a.model}:{a.outcome}" + (f" ({a.detail})" if a.detail and not a.ok else "")
        for a in attempts
    )


__all__ = [
    "AttemptRecord",
    "AUTH_STATUS",
    "CircuitBreaker",
    "CONFIG_STATUS",
    "ErrorClass",
    "OnAttempt",
    "ResiliencePolicy",
    "TRANSIENT_STATUS",
    "classify_error",
    "is_auth_error",
    "summarize_attempts",
]
