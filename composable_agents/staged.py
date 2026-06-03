"""Plan validation for the Staged shape (blueprint §8).

``eval_plan`` lets a *brain* emit structure at runtime — a Plan — which is then
compiled to ordinary IR and run. That is the framework's sharpest edge: model
output becomes control flow. §8 is the firewall that keeps it bounded. Before a
compiled plan is admitted it must clear hard rules that the parent's grants pin
down, none of which the model can talk its way past:

* **bounded** — ``closed_shape(plan) <= Feedback``. A plan may loop (Feedback)
  but may not itself stage another plan (Staged) or open an agent loop (Agent),
  directly or by revealing a richer ``Sub`` contract. Recursion is capped at one
  level of model-authored structure.
* **granted tools only** — every tool the plan calls must already be in the
  parent capability manifest. A plan cannot reach a tool the parent couldn't.
* **no budget raise** — the plan's estimated cost must fit the parent budget; a
  plan can spend down, never expand, the envelope.
* **well-formed + type-safe** — the plan must pass ordinary
  :func:`composable_agents.validate.validate` (structure, ids, seq-edge schemas).

:func:`validate_plan` returns diagnostics; :func:`admit_plan` raises
:class:`~composable_agents.errors.PlanRejected` if any are blocking, and is what
the ``compilePlan`` activity calls before letting the harness run the plan.
"""

from __future__ import annotations

from typing import Optional

from .capabilities import CapabilityManifest
from .contracts import ToolManifest
from .errors import PlanRejected
from .ir import CallStep, Node, SubStep, ThinkStep, toolref_key
from .kinds import Op, Shape, shape_rank
from .shapes import closed_shape
from .validate import Diagnostic, blocking, validate

# Rough per-leaf cost (in the same units as Ann.cost / Budget.usd) used only when
# a node carries no explicit cost annotation. Deliberately small and overridable.
_DEFAULT_CALL_COST = 1.0
_DEFAULT_THINK_COST = 2.0
_DEFAULT_SUB_COST = 5.0


def estimate_cost(plan: Node) -> float:
    """A conservative upper-bound cost for a plan, folding structure.

    ``seq``/``par`` sum their children (every branch runs), ``alt`` takes the max
    (one branch is chosen), ``iter_up_to`` multiplies its body by the bound. Pure
    leaves (``ident``/``arr``) are free. Explicit ``Ann.cost`` always wins for a
    node. Used to enforce "no budget raise" without executing anything.
    """
    op = plan.op
    own = plan.ann.cost if (plan.ann and plan.ann.cost is not None) else None

    if op == Op.PRIM:
        step = plan.step
        if own is not None:
            return own
        if isinstance(step, ThinkStep):
            return _DEFAULT_THINK_COST
        if isinstance(step, SubStep):
            return _DEFAULT_SUB_COST
        return _DEFAULT_CALL_COST
    if op in (Op.IDENT, Op.ARR):
        return own or 0.0
    if op == Op.SEQ:
        base = estimate_cost(plan.left) + estimate_cost(plan.right) if plan.left and plan.right else 0.0
        return (own or 0.0) + base
    if op == Op.PAR:
        base = estimate_cost(plan.left) + estimate_cost(plan.right) if plan.left and plan.right else 0.0
        return (own or 0.0) + base
    if op == Op.ALT:
        base = max(estimate_cost(plan.left), estimate_cost(plan.right)) if plan.left and plan.right else 0.0
        return (own or 0.0) + base
    if op == Op.ITER_UP_TO:
        body = estimate_cost(plan.body) if plan.body else 0.0
        bound = plan.bound or 1
        return (own or 0.0) + bound * body
    # eval_plan / app should never appear in a bounded plan; charge their own ann
    # if present so an illegal plan still produces a finite number.
    return own or _DEFAULT_SUB_COST


def referenced_tool_keys(plan: Node) -> list[str]:
    """Toolref keys (``name`` or ``server/tool``) the plan calls, de-duplicated."""
    keys: list[str] = []
    seen: set[str] = set()
    for n in plan.walk():
        if isinstance(n.step, CallStep):
            k = toolref_key(n.step.tool)
            if k not in seen:
                seen.add(k)
                keys.append(k)
    return keys


def validate_plan(
    plan: Node,
    parent: CapabilityManifest,
    manifest: Optional[ToolManifest] = None,
) -> list[Diagnostic]:
    """Diagnostics for a compiled plan against the parent's grants (§8).

    Pass ``manifest`` (the parent flow's frozen manifest) to enable the
    schema/manifest-resolution checks inside :func:`validate`; structural and
    capability checks run regardless.
    """
    out: list[Diagnostic] = []

    # Inherit ordinary well-formedness, ids, and (if manifest given) schema edges.
    out.extend(validate(plan, manifest))

    # Bounded shape: a plan may loop but may not stage or app.
    s = closed_shape(plan)
    if shape_rank(s) > shape_rank(Shape.FEEDBACK):
        out.append(
            Diagnostic(
                "PLAN_TOO_RICH",
                plan.id,
                f"staged plan has closed shape {s.value} (> Feedback); a plan may "
                "not stage another plan or open an agent loop",
            )
        )

    # Granted tools only: the plan can't reach past the parent's tool grants.
    for n in plan.walk():
        if isinstance(n.step, CallStep):
            key = toolref_key(n.step.tool)
            if key not in parent.tools:
                out.append(
                    Diagnostic(
                        "PLAN_TOOL_UNGRANTED",
                        n.id,
                        f"plan calls {key!r}, which the parent capability manifest "
                        "does not grant",
                    )
                )
        # A plan may not promote a child to Agent/Staged via a Sub contract.
        if isinstance(n.step, SubStep):
            cs = n.step.contract.shape
            if shape_rank(cs) > shape_rank(Shape.FEEDBACK):
                out.append(
                    Diagnostic(
                        "PLAN_SUB_TOO_RICH",
                        n.id,
                        f"plan spawns a sub with contract shape {cs.value} "
                        "(> Feedback); not allowed inside a staged plan",
                    )
                )

    # No budget raise: estimated spend must fit the parent envelope.
    if parent.budget is not None and parent.budget.usd is not None:
        est = estimate_cost(plan)
        if est > parent.budget.usd:
            out.append(
                Diagnostic(
                    "PLAN_BUDGET",
                    plan.id,
                    f"plan estimated cost {est:.2f} exceeds parent budget "
                    f"{parent.budget.usd:.2f}",
                )
            )

    return out


def admit_plan(
    plan: Node,
    parent: CapabilityManifest,
    manifest: Optional[ToolManifest] = None,
) -> None:
    """Raise :class:`PlanRejected` if ``plan`` has any blocking §8 violation."""
    diags = validate_plan(plan, parent, manifest)
    bad = blocking(diags)
    if bad:
        raise PlanRejected(f"[{d.code}@{d.node_id}] {d.message}" for d in bad)
