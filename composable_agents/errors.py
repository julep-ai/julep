"""Exception types."""

from __future__ import annotations


class ComposableAgentsError(Exception):
    """Base for everything this framework raises."""


class ValidationError(ComposableAgentsError):
    """Raised at deploy when ``validate`` finds blocking diagnostics."""

    def __init__(self, diagnostics):  # diagnostics: list[Diagnostic]
        self.diagnostics = diagnostics
        msg = "; ".join(f"[{d.code}@{d.node_id}] {d.message}" for d in diagnostics)
        super().__init__(f"flow failed validation: {msg}")


class FreezeError(ComposableAgentsError):
    """Raised when a ToolRef can't be resolved against the MCP snapshot."""


class AdmissionError(ComposableAgentsError):
    """A branch is illegal in a race/hedge/quorum position (§5 guarantee)."""


class BudgetExceeded(ComposableAgentsError):
    """The Agent budget guard or a plan's budget estimate was exceeded."""


class PlanRejected(ComposableAgentsError):
    """A model-generated plan violated a hard rule (blueprint §8)."""

    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("plan rejected: " + "; ".join(self.reasons))


class CapabilityDenied(ComposableAgentsError):
    """A capability-manifest gate (compile/schedule/run) refused."""
