"""The App agent loop and plan extraction (blueprint §P4), kept pure.

``Agent`` sits at the top of the shape lattice: an open-ended controller loop
that decides, round by round, what to do next. Two things keep that from being a
licence for unbounded, unsafe execution:

* **Bounded actions.** A controller does not emit arbitrary IR to run inline.
  Each round it returns one of a small, closed set of decisions
  (:func:`interpret_brain_reply`): *finish*, *escalate*, call one *granted tool*,
  or invoke one pre-registered *sub-flow*. Anything richer is the planner's job,
  not the agent's. This is what lets the loop run under Temporal without freezing
  and admitting fresh IR mid-flight.
* **A budget guard.** Every round charges an estimated cost; when the running
  total would exceed the capability budget (§9) the loop stops with
  ``over_budget`` instead of continuing. History growth is bounded separately by
  continue-as-new (:func:`should_continue_as_new`), the §6 seam the harness wires.

Plan *extraction* is the offline complement: an observed action trace is
generalized into a candidate Plan (:func:`generalize_trace_to_plan`) which is
then run through §8 admission (:func:`extract_plan`) before it may be promoted to
a cheap, replayable :func:`~composable_agents.dsl.stage`. The agent discovers a
procedure; the plan freezes it.

Everything here is dependency-free and deterministic so the loop's control logic
is unit-testable without a Temporal server; the durable wrapper that adds
activities and continue-as-new lives in :mod:`composable_agents.execution.harness`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .capabilities import Budget, CapabilityManifest
from .contracts import ToolManifest
from .dsl import Contract, call, ident, pipeline, subagent
from .errors import PlanRejected
from .ir import Node
from .kinds import Shape
from .staged import admit_plan, estimate_cost, validate_plan
from .validate import Diagnostic


# --------------------------------------------------------------------------- #
# Round decisions.
# --------------------------------------------------------------------------- #
class Decision(str, Enum):
    """What a controller asked the loop to do this round."""

    FINISH = "finish"      # done: payload is the final output
    ESCALATE = "escalate"  # give up to a human/parent: payload is a reason
    CALL = "call"          # invoke a granted tool: payload is {"tool", "input"}
    SUB = "sub"            # invoke a registered sub-flow: payload is {"ref", "input", "shape"?}


# Default per-action cost estimate (USD), used when the controller does not
# report an actual cost. Deliberately conservative so the budget guard trips
# early rather than late. Matches the structural defaults in ``staged``.
DEFAULT_TOOL_COST = 1.0
DEFAULT_SUB_COST = 5.0
DEFAULT_THINK_COST = 2.0  # the controller's own per-round model call


@dataclass(frozen=True)
class RoundAction:
    """A normalized, validated controller decision for one round."""

    decision: Decision
    payload: Any = None

    @property
    def is_terminal(self) -> bool:
        return self.decision in (Decision.FINISH, Decision.ESCALATE)


def interpret_brain_reply(reply: Any) -> RoundAction:
    """Map a controller's structured reply to a :class:`RoundAction`.

    Accepts the small, closed action vocabulary the loop supports. A reply that
    does not match any known shape is treated as a *finish* carrying the raw
    reply as output — a controller that just answers in prose ends the loop
    rather than erroring, which is the least-surprising default.
    """
    if not isinstance(reply, dict):
        return RoundAction(Decision.FINISH, reply)

    # Finish: explicit done flag, or a bare {"output": ...}.
    if reply.get("done") is True or ("output" in reply and "tool" not in reply and "sub" not in reply):
        return RoundAction(Decision.FINISH, reply.get("output", reply))

    if "escalate" in reply:
        return RoundAction(Decision.ESCALATE, reply.get("escalate") or "escalated by controller")

    if "tool" in reply:
        return RoundAction(
            Decision.CALL,
            {"tool": reply["tool"], "input": reply.get("input", reply.get("args"))},
        )

    if "sub" in reply:
        return RoundAction(
            Decision.SUB,
            {
                "ref": reply["sub"],
                "input": reply.get("input"),
                "shape": reply.get("shape", Shape.PIPELINE.value),
            },
        )

    # Unknown shape: end cleanly with whatever the controller produced.
    return RoundAction(Decision.FINISH, reply)


def action_cost(action: RoundAction, reported: Optional[float] = None) -> float:
    """Cost to charge for an action this round (controller-reported or default)."""
    if reported is not None:
        return float(reported)
    if action.decision is Decision.CALL:
        return DEFAULT_TOOL_COST
    if action.decision is Decision.SUB:
        return DEFAULT_SUB_COST
    return 0.0


# --------------------------------------------------------------------------- #
# Loop config + state (continue-as-new safe: fully JSON round-trippable).
# --------------------------------------------------------------------------- #
@dataclass
class AgentConfig:
    """Static policy for an agent run."""

    max_rounds: int = 24
    budget: Optional[Budget] = None
    # §6 seam: after this many rounds, the durable harness calls continue_as_new
    # to truncate Temporal history. 0 disables (history grows unbounded — fine
    # for short agents, a footgun for long ones).
    continue_as_new_after: int = 0
    # Per-round controller call cost, charged in addition to the action.
    think_cost: float = DEFAULT_THINK_COST

    @staticmethod
    def from_json(d: dict[str, Any]) -> "AgentConfig":
        return AgentConfig(
            max_rounds=int(d.get("maxRounds", d.get("max_rounds", 24))),
            budget=Budget.from_dict(d.get("budget")),
            continue_as_new_after=int(
                d.get("continueAsNewAfter", d.get("continue_as_new_after", 0))
            ),
            think_cost=float(d.get("thinkCost", d.get("think_cost", DEFAULT_THINK_COST))),
        )

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "maxRounds": self.max_rounds,
            "continueAsNewAfter": self.continue_as_new_after,
            "thinkCost": self.think_cost,
        }
        if self.budget is not None:
            b: dict[str, Any] = {}
            if self.budget.usd is not None:
                b["usd"] = self.budget.usd
            if self.budget.tokens is not None:
                b["tokens"] = self.budget.tokens
            if self.budget.wall_seconds is not None:
                b["wallSeconds"] = self.budget.wall_seconds
            out["budget"] = b
        return out

    @staticmethod
    def from_capabilities(caps: Optional[CapabilityManifest], **overrides: Any) -> "AgentConfig":
        cfg = AgentConfig(budget=caps.budget if caps else None)
        for k, v in overrides.items():
            setattr(cfg, k, v)
        return cfg


@dataclass
class TraceEntry:
    """One recorded action and its result (the raw material for plan extraction)."""

    decision: str
    ref: Optional[str] = None      # tool name or sub-flow ref
    shape: Optional[str] = None    # sub-flow surface shape, if a sub
    cost: float = 0.0

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"decision": self.decision, "cost": self.cost}
        if self.ref is not None:
            out["ref"] = self.ref
        if self.shape is not None:
            out["shape"] = self.shape
        return out

    @staticmethod
    def from_json(d: dict[str, Any]) -> "TraceEntry":
        return TraceEntry(
            decision=d["decision"], ref=d.get("ref"),
            shape=d.get("shape"), cost=float(d.get("cost", 0.0)),
        )


@dataclass
class AgentState:
    """Mutable loop state. Round-trips through JSON for continue-as-new."""

    round: int = 0
    spent_usd: float = 0.0
    last: Any = None
    trace: list[TraceEntry] = field(default_factory=list)

    def charge(self, usd: float) -> None:
        self.spent_usd += usd

    def record(self, entry: TraceEntry) -> None:
        self.trace.append(entry)

    def to_json(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "spentUsd": self.spent_usd,
            "last": self.last,
            "trace": [t.to_json() for t in self.trace],
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> "AgentState":
        return AgentState(
            round=int(d.get("round", 0)),
            spent_usd=float(d.get("spentUsd", 0.0)),
            last=d.get("last"),
            trace=[TraceEntry.from_json(t) for t in d.get("trace", [])],
        )


# --------------------------------------------------------------------------- #
# Budget + continue-as-new policy (pure predicates the harness consults).
# --------------------------------------------------------------------------- #
def would_exceed_budget(state: AgentState, next_cost: float, budget: Optional[Budget]) -> bool:
    """True if charging ``next_cost`` would push the run over its USD budget."""
    if budget is None or budget.usd is None:
        return False
    return state.spent_usd + next_cost > budget.usd


def should_continue_as_new(state: AgentState, cfg: AgentConfig) -> bool:
    """True when the durable harness should truncate history via continue-as-new."""
    return cfg.continue_as_new_after > 0 and state.round >= cfg.continue_as_new_after


def terminal_result(status: str, state: AgentState, output: Any = None,
                    reason: Optional[str] = None) -> dict[str, Any]:
    """Uniform shape for everything the agent loop can return."""
    out: dict[str, Any] = {
        "status": status,
        "output": output if output is not None else state.last,
        "rounds": state.round,
        "spentUsd": state.spent_usd,
        "trace": [t.to_json() for t in state.trace],
    }
    if reason is not None:
        out["reason"] = reason
    return out


# --------------------------------------------------------------------------- #
# Plan extraction (offline generalization of an observed trace).
# --------------------------------------------------------------------------- #
def generalize_trace_to_plan(trace: list[TraceEntry]) -> Node:
    """Turn a successful action trace into a candidate Plan (straight-line IR).

    Calls become :func:`~composable_agents.dsl.call` leaves and sub-flow
    invocations become :func:`~composable_agents.dsl.subagent` leaves, chained in
    observed order with :func:`~composable_agents.dsl.pipeline`. Terminal
    decisions (finish/escalate) carry no tool and are skipped. The result is a
    *candidate* only — it must clear :func:`extract_plan` before promotion.

    The generalization is deliberately shallow (a pipeline, never a loop or a
    stage), which keeps every extracted plan within the ``<= Feedback`` ceiling
    that §8 admission enforces.
    """
    leaves: list[Node] = []
    for t in trace:
        if t.decision == Decision.CALL.value and t.ref:
            leaves.append(call(t.ref))
        elif t.decision == Decision.SUB.value and t.ref:
            shape = Shape(t.shape) if t.shape else Shape.PIPELINE
            leaves.append(subagent(t.ref, Contract.of(shape)))
    if not leaves:
        return ident()
    if len(leaves) == 1:
        return leaves[0]
    return pipeline(*leaves)


def extract_plan(
    trace: list[TraceEntry],
    parent: CapabilityManifest,
    manifest: Optional[ToolManifest] = None,
) -> tuple[Node, list[Diagnostic]]:
    """Generalize ``trace`` to a plan and return it with its §8 diagnostics.

    Does not raise: a caller inspecting whether an observed agent run is safe to
    promote wants the diagnostics, not an exception. Use :func:`promote_plan`
    when you want admission to be enforced.
    """
    plan = generalize_trace_to_plan(trace)
    diags = validate_plan(plan, parent, manifest)
    return plan, diags


def promote_plan(
    trace: list[TraceEntry],
    parent: CapabilityManifest,
    manifest: Optional[ToolManifest] = None,
) -> Node:
    """Generalize and admit an observed trace, returning the promotable plan.

    Raises :class:`~composable_agents.errors.PlanRejected` if the generalized
    plan would not pass §8 admission (e.g. it references an ungranted tool or
    exceeds the budget), mirroring runtime plan staging exactly.
    """
    plan = generalize_trace_to_plan(trace)
    admit_plan(plan, parent, manifest)  # raises PlanRejected on any blocking diag
    return plan


__all__ = [
    "Decision",
    "RoundAction",
    "interpret_brain_reply",
    "action_cost",
    "AgentConfig",
    "AgentState",
    "TraceEntry",
    "would_exceed_budget",
    "should_continue_as_new",
    "terminal_result",
    "generalize_trace_to_plan",
    "extract_plan",
    "promote_plan",
    "estimate_cost",
    "PlanRejected",
]
