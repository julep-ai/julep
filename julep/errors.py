"""Exception types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

# resilience is stdlib-only and must never import errors (one-way dependency).
from .resilience import summarize_attempts

if TYPE_CHECKING:
    from .resilience import AttemptRecord
    from .validate import Diagnostic


class JulepError(Exception):
    """Base for everything this framework raises."""


class SessionTurnError(JulepError):
    """Explicit per-turn session error signal.

    ``fatal=False`` lets a live session report the failed turn and continue to
    the next receive without advancing the carrier.
    """

    def __init__(self, message: str, *, fatal: bool = False) -> None:
        self.fatal = fatal
        super().__init__(message)


class ValidationError(JulepError):
    """Raised at deploy when ``validate`` finds blocking diagnostics."""

    def __init__(self, diagnostics: list["Diagnostic"]) -> None:
        self.diagnostics = diagnostics
        msg = "; ".join(f"[{d.code}@{d.node_id}] {d.message}" for d in diagnostics)
        super().__init__(f"flow failed validation: {msg}")


class FreezeError(JulepError):
    """Raised when a ToolRef can't be resolved against the MCP snapshot."""


class PureDriftError(JulepError):
    """Raised when a pinned pure source hash no longer matches the worker registry."""


class ToolSurfaceDrift(JulepError):
    """A frozen MCP call no longer exists or rejects its frozen input shape."""

    def __init__(self, server: str, tool: str, reason: str) -> None:
        self.server = server
        self.tool = tool
        self.reason = reason
        super().__init__(f"MCP tool surface drift for {server}/{tool}: {reason}")

    def to_json(self) -> dict[str, str]:
        return {"server": self.server, "tool": self.tool, "reason": self.reason}


class ToolInputValidation(JulepError):
    """Tool arguments failed the release's frozen input schema before network IO."""

    def __init__(self, server: str, tool: str) -> None:
        self.server = server
        self.tool = tool
        super().__init__(f"tool input failed frozen schema validation for {server}/{tool}")


def tool_surface_drift_from_cause(error: BaseException) -> ToolSurfaceDrift | None:
    """Find or reconstruct typed drift through an engine exception chain.

    Temporal's workflow sandbox can call this helper without importing the
    Temporal SDK.  Activity failures expose the application error type on a
    nested cause; direct/local backends preserve the original exception.
    """

    pending: list[BaseException] = [error]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        if isinstance(current, ToolSurfaceDrift):
            return current
        error_type = getattr(current, "type", None)
        if error_type == "ToolSurfaceDrift" or type(current).__name__ == "ToolSurfaceDrift":
            message = str(current)
            marker = "MCP tool surface drift for "
            if marker in message:
                target_and_reason = message.split(marker, 1)[1]
                target, separator, reason = target_and_reason.partition(": ")
                server, slash, tool = target.partition("/")
                if separator and slash and server and tool and reason:
                    return ToolSurfaceDrift(server, tool, reason)
            return ToolSurfaceDrift("<activity>", "<unknown>", message)
        for nested in (
            getattr(current, "__cause__", None),
            getattr(current, "__context__", None),
            getattr(current, "cause", None),
        ):
            if isinstance(nested, BaseException):
                pending.append(nested)
    return None


class PureExecutionError(JulepError):
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


class AdmissionError(JulepError):
    """A branch is illegal in a race/hedge/quorum position (§5 guarantee)."""


class RaceAllFailed(JulepError):
    """A race/hedge/quorum group could not reach its required successes."""

    def __init__(self, failures: Iterable[BaseException]) -> None:
        self.failures = list(failures)
        super().__init__(f"race-family group failed with {len(self.failures)} branch failure(s)")


class UnsupportedShapeError(JulepError):
    """The flow uses an operator this execution backend cannot run.

    Raised at dispatch time (pre-execution IR scan), never mid-run: a flow that
    starts on a backend always finishes there or fails for a different reason.
    """


class BudgetExceeded(JulepError):
    """The Agent budget guard or a plan's budget estimate was exceeded."""


class PlanRejected(JulepError):
    """A model-generated plan violated a hard rule (blueprint §8)."""

    def __init__(self, reasons: Iterable[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("plan rejected: " + "; ".join(self.reasons))


class CapabilityDenied(JulepError):
    """A capability-manifest gate (compile/schedule/run) refused."""


class PrincipalRequired(JulepError):
    """A worker caller required a run principal and the run supplied none.

    Raised by worker-supplied callers (never by the framework itself); a settled
    policy decision, so it is non-retryable like :class:`CapabilityDenied`.
    """


POLICY_ERRORS: tuple[type[JulepError], ...] = (
    CapabilityDenied,
    PlanRejected,
    ValidationError,
    FreezeError,
    PureDriftError,
    ToolSurfaceDrift,
    ToolInputValidation,
    PrincipalRequired,
)
"""Settled policy decisions that execution backends must never retry."""


class ResilienceExhausted(JulepError):
    """Every candidate model in a resilience fallback chain failed or was skipped.

    Carries the full per-attempt record so callers (and observability sinks)
    can see exactly which models were tried, in what order, and why each lost.
    """

    def __init__(self, attempts: list["AttemptRecord"]) -> None:
        self.attempts = attempts
        super().__init__(
            f"all {len(attempts)} model attempt(s) failed: {summarize_attempts(attempts)}"
        )
