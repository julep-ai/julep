"""Exception types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from .validate import Diagnostic


class ComposableAgentsError(Exception):
    """Base for everything this framework raises."""


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
