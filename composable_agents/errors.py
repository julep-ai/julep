"""Exception types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

# resilience is stdlib-only and must never import errors (one-way dependency).
from .resilience import summarize_attempts

if TYPE_CHECKING:
    from .resilience import AttemptRecord
    from .validate import Diagnostic


class ComposableAgentsError(Exception):
    """Base for everything this framework raises."""


class SessionTurnError(ComposableAgentsError):
    """Explicit per-turn session error signal.

    ``fatal=False`` lets a live session report the failed turn and continue to
    the next receive without advancing the carrier.
    """

    def __init__(self, message: str, *, fatal: bool = False) -> None:
        self.fatal = fatal
        super().__init__(message)


class ValidationError(ComposableAgentsError):
    """Raised at deploy when ``validate`` finds blocking diagnostics."""

    def __init__(self, diagnostics: list["Diagnostic"]) -> None:
        self.diagnostics = diagnostics
        msg = "; ".join(f"[{d.code}@{d.node_id}] {d.message}" for d in diagnostics)
        super().__init__(f"flow failed validation: {msg}")


class FreezeError(ComposableAgentsError):
    """Raised when a ToolRef can't be resolved against the MCP snapshot."""


class PureDriftError(ComposableAgentsError):
    """Raised when a pinned pure source hash no longer matches the worker registry."""


class PureExecutionError(ComposableAgentsError):
    """A bundle-sourced pure raised inside the wasm sandbox.

    Carries the in-sandbox error_type and message plus a short traceback tail
    so flow error semantics match a native pure raising the same exception.
    """

    def __init__(
        self,
        error_type: str,
        message: str,
        traceback_tail: list[str] | None = None,
    ) -> None:
        self.error_type = error_type
        self.message = message
        self.traceback_tail = list(traceback_tail or [])
        super().__init__(f"{error_type}: {message}")


class AdmissionError(ComposableAgentsError):
    """A branch is illegal in a race/hedge/quorum position (§5 guarantee)."""


class RaceAllFailed(ComposableAgentsError):
    """A race/hedge/quorum group could not reach its required successes."""

    def __init__(self, failures: Iterable[BaseException]) -> None:
        self.failures = list(failures)
        super().__init__(f"race-family group failed with {len(self.failures)} branch failure(s)")


class UnsupportedShapeError(ComposableAgentsError):
    """The flow uses an operator this execution backend cannot run.

    Raised at dispatch time (pre-execution IR scan), never mid-run: a flow that
    starts on a backend always finishes there or fails for a different reason.
    """


class BudgetExceeded(ComposableAgentsError):
    """The Agent budget guard or a plan's budget estimate was exceeded."""


class PlanRejected(ComposableAgentsError):
    """A model-generated plan violated a hard rule (blueprint §8)."""

    def __init__(self, reasons: Iterable[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("plan rejected: " + "; ".join(self.reasons))


class CapabilityDenied(ComposableAgentsError):
    """A capability-manifest gate (compile/schedule/run) refused."""


class PrincipalRequired(ComposableAgentsError):
    """A worker caller required a run principal and the run supplied none.

    Raised by worker-supplied callers (never by the framework itself); a settled
    policy decision, so it is non-retryable like :class:`CapabilityDenied`.
    """


POLICY_ERRORS: tuple[type[ComposableAgentsError], ...] = (
    CapabilityDenied,
    PlanRejected,
    ValidationError,
    FreezeError,
    PureDriftError,
    PrincipalRequired,
)
"""Settled policy decisions that execution backends must never retry."""


class ResilienceExhausted(ComposableAgentsError):
    """Every candidate model in a resilience fallback chain failed or was skipped.

    Carries the full per-attempt record so callers (and observability sinks)
    can see exactly which models were tried, in what order, and why each lost.
    """

    def __init__(self, attempts: list["AttemptRecord"]) -> None:
        self.attempts = attempts
        super().__init__(
            f"all {len(attempts)} model attempt(s) failed: {summarize_attempts(attempts)}"
        )
