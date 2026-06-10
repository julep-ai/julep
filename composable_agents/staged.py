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
from .contracts import FrozenTool, ToolManifest
from .errors import PlanRejected
from .ir import CallStep, Node, SubStep, ThinkStep, toolref_key
from .kinds import Op, Shape, shape_rank
from .shapes import closed_shape
from .validate import Diagnostic, blocking, validate

# Rough per-leaf cost (in the same units as Ann.cost / Budget.cost) used only when
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
        if plan.cases is not None:
            branch_costs = [estimate_cost(plan.cases[k]) for k in sorted(plan.cases)]
            if plan.default is not None:
                branch_costs.append(estimate_cost(plan.default))
            base = max(branch_costs) if branch_costs else 0.0
        else:
            base = max(estimate_cost(plan.left), estimate_cost(plan.right)) if plan.left and plan.right else 0.0
        return (own or 0.0) + base
    if op == Op.ITER_UP_TO:
        body = estimate_cost(plan.body) if plan.body else 0.0
        bound = plan.bound or 1
        return (own or 0.0) + bound * body
    # each / eval_plan / app should never appear in a bounded plan (each's cost
    # scales with runtime data); charge their own ann if present so an illegal
    # plan still produces a finite number.
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


def _copy_plan(plan: Node) -> Node:
    """Deep-copy a finite plan through its JSON representation."""
    return Node.from_json(plan.to_json())


def _binding_reasons(diags: list[Diagnostic]) -> list[str]:
    return [f"[{d.code}@{d.node_id}] {d.message}" for d in diags]


def _bind_plan_to_manifest(
    plan: Node,
    manifest: ToolManifest,
) -> tuple[Node, list[Diagnostic]]:
    bound = _copy_plan(plan)
    out: list[Diagnostic] = []

    by_key: dict[str, list[FrozenTool]] = {}
    for entry in manifest.values():
        by_key.setdefault(toolref_key(entry.ref), []).append(entry)

    for n in bound.walk():
        step = n.step
        if not isinstance(step, CallStep):
            continue

        key = toolref_key(step.tool)
        pinned = step.frozen_hash

        if pinned is not None:
            pinned_entry = manifest.get(pinned)
            if pinned_entry is None:
                out.append(
                    Diagnostic(
                        "PLAN_TOOL_UNBOUND",
                        n.id,
                        f"plan pins {key!r} to {pinned}, which is absent from "
                        "the parent frozen manifest",
                    )
                )
                continue
            if toolref_key(pinned_entry.ref) != key:
                out.append(
                    Diagnostic(
                        "PLAN_TOOL_UNBOUND",
                        n.id,
                        f"plan pins {key!r} to {pinned}, but that manifest entry "
                        f"is {toolref_key(pinned_entry.ref)!r}",
                    )
                )
                continue
            step.frozen_hash = pinned_entry.execution_hash
            continue

        matches = by_key.get(key, [])
        if not matches:
            out.append(
                Diagnostic(
                    "PLAN_TOOL_UNBOUND",
                    n.id,
                    f"plan calls {key!r}, which is absent from the parent frozen manifest",
                )
            )
        elif len(matches) > 1:
            choices = ", ".join(entry.execution_hash for entry in matches)
            out.append(
                Diagnostic(
                    "PLAN_TOOL_AMBIGUOUS",
                    n.id,
                    f"plan calls {key!r}, which matches multiple parent manifest "
                    f"entries: {choices}",
                )
            )
        else:
            matched_entry = matches[0]
            step.frozen_hash = matched_entry.execution_hash

    return bound, out


def bind_plan_to_manifest(plan: Node, manifest: ToolManifest) -> Node:
    """Return a copy of ``plan`` whose calls are bound to ``manifest`` hashes.

    Staged plans are authored with logical :class:`ToolRef` values, but runtime
    scheduling needs the parent's frozen contracts. Each call is matched by
    ``toolref_key`` and receives the corresponding ``FrozenTool.execution_hash``.
    Ambiguous logical refs must be hash-pinned by the plan; unknown or stale
    pins reject the plan.
    """
    bound, diags = _bind_plan_to_manifest(plan, manifest)
    bad = blocking(diags)
    if bad:
        raise PlanRejected(_binding_reasons(bad))
    return bound


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
    checked = plan
    binding_diags: list[Diagnostic] = []

    if manifest is not None:
        checked, binding_diags = _bind_plan_to_manifest(plan, manifest)
        out.extend(binding_diags)

    # Inherit ordinary well-formedness, ids, and (if manifest given) schema edges.
    out.extend(validate(checked, manifest if not blocking(binding_diags) else None))

    # Bounded shape: a plan may loop but may not stage or app.
    s = closed_shape(checked)
    if shape_rank(s) > shape_rank(Shape.FEEDBACK):
        out.append(
            Diagnostic(
                "PLAN_TOO_RICH",
                checked.id,
                f"staged plan has closed shape {s.value} (> Feedback); a plan may "
                "not stage another plan or open an agent loop",
            )
        )

    # Dynamic fan-out is unbounded by construction: `each` multiplies its body
    # by the runtime list length, which admission cannot see. A plan that wants
    # repetition must use iter_up_to with a literal bound.
    for n in checked.walk():
        if n.op == Op.EACH:
            out.append(
                Diagnostic(
                    "PLAN_DYNAMIC_FANOUT",
                    n.id,
                    "staged plan contains `each` (dynamic fan-out); its cost "
                    "scales with runtime data and cannot be admitted. Use "
                    "iter_up_to with a literal bound instead",
                )
            )

    # Granted tools only: the plan can't reach past the parent's tool grants.
    for n in checked.walk():
        if isinstance(n.step, CallStep):
            key = toolref_key(n.step.tool)
            if parent._has_tools and key not in parent.tools:
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
    if parent.budget is not None and parent.budget.cost is not None:
        est = estimate_cost(checked)
        if est > parent.budget.cost:
            out.append(
                Diagnostic(
                    "PLAN_BUDGET",
                    checked.id,
                    f"plan estimated cost {est:.2f} exceeds parent budget "
                    f"{parent.budget.cost:.2f}",
                )
            )

    return out


def admit_plan(
    plan: Node,
    parent: CapabilityManifest,
    manifest: Optional[ToolManifest] = None,
) -> Node:
    """Return the admitted plan, or raise ``PlanRejected`` on blocking diagnostics."""
    bound = plan
    if manifest is not None:
        bound, binding_diags = _bind_plan_to_manifest(plan, manifest)
        bad = blocking(binding_diags)
        if bad:
            raise PlanRejected(_binding_reasons(bad))

    diags = validate_plan(bound, parent, manifest)
    bad = blocking(diags)
    if bad:
        raise PlanRejected(f"[{d.code}@{d.node_id}] {d.message}" for d in bad)
    return bound
