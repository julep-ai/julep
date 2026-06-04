"""validate(): the submit-time gate (blueprint §1.4).

Returns a list of :class:`Diagnostic`. The flow may deploy iff there are no
``error``-severity diagnostics. ``warning`` diagnostics (e.g. a ``par`` branch
that will be degraded to sequential because it reads the whole session) are
informational and answer questions like "why did my fan-out serialize".

Rules implemented:

* finite tree / no host-language knots
* per-op structural well-formedness
* unique node ids (so the projection's ``causes`` are unambiguous)
* ``eval_plan.plan`` has ``surface_shape <= Feedback``
* ``seq`` edge type-checks: ``outputSchema(left) ⊑ inputSchema(right)`` where both
  ends are typed calls (conservative — unknown schemas are skipped, not failed)
* ``ContextPolicy`` legality: a ``WHOLE_SESSION`` branch under ``par`` is flagged
  for sequential degrade
* named-``Pure``: ``arr``/``alt`` must carry a registered ``pure`` (no inline closures)
* post-freeze: every ``call`` resolves to a manifest entry
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .contracts import ToolManifest
from .ir import (
    CallStep,
    ContextPolicy,
    JSONSchema,
    Node,
    ThinkStep,
)
from .kinds import ContextScope, Op, Shape, shape_leq
from .purity import is_registered
from .shapes import surface_shape
from .transforms import collect_duplicate_ids, detect_cycles


@dataclass
class Diagnostic:
    code: str
    node_id: str
    message: str
    severity: str = "error"  # "error" | "warning"


def blocking(diags: list[Diagnostic]) -> list[Diagnostic]:
    return [d for d in diags if d.severity == "error"]


# --------------------------------------------------------------------------- #
# Conservative JSON-Schema subtyping for seq edges.
# --------------------------------------------------------------------------- #
def schema_incompatibility(out: Optional[JSONSchema], inp: Optional[JSONSchema]) -> Optional[str]:
    """Return a reason if ``out`` definitely can't satisfy ``inp``, else None.

    Deliberately conservative: anything we can't prove incompatible passes
    (returns None) so we never block on schemas we can't see.
    """
    if not out or not inp:
        return None
    ot, it = out.get("type"), inp.get("type")
    if ot and it and ot != it:
        # object-vs-object with extra/optional fields is fine; a string feeding
        # an object-expecting input is not.
        return f"producer type {ot!r} != consumer type {it!r}"
    if it == "object" and out.get("type") == "object":
        required = inp.get("required") or []
        props = out.get("properties") or {}
        if props:  # only judge when the producer declares its properties
            missing = [r for r in required if r not in props]
            if missing:
                return f"missing required field(s): {', '.join(missing)}"
    return None


def _entry_schema(n: Node, manifest: Optional[ToolManifest]) -> Optional[JSONSchema]:
    """Input schema of the first leaf to receive the value, if knowable."""
    if manifest is None:
        return None
    op = n.op
    if op == Op.PRIM and isinstance(n.step, CallStep) and n.step.frozen_hash:
        tool = manifest.get(n.step.frozen_hash)
        return tool.input_schema if tool else None
    if op == Op.SEQ:
        return _entry_schema(n.left, manifest)
    if op == Op.ITER_UP_TO:
        return _entry_schema(n.body, manifest)
    return None  # par / alt / think / sub / ident / arr / staged / agent: unknown


def _exit_schema(n: Node, manifest: Optional[ToolManifest]) -> Optional[JSONSchema]:
    """Output schema of the last leaf to produce the value, if knowable."""
    if manifest is None:
        return None
    op = n.op
    if op == Op.PRIM and isinstance(n.step, CallStep) and n.step.frozen_hash:
        tool = manifest.get(n.step.frozen_hash)
        return tool.output_schema if tool else None
    if op == Op.SEQ:
        return _exit_schema(n.right, manifest)
    if op == Op.ITER_UP_TO:
        return _exit_schema(n.body, manifest)
    return None


# --------------------------------------------------------------------------- #
# Per-op structural well-formedness.
# --------------------------------------------------------------------------- #
def _check_structure(n: Node, out: list[Diagnostic]) -> None:
    op = n.op

    def err(code: str, msg: str) -> None:
        out.append(Diagnostic(code, n.id, msg))

    has_lr = n.left is not None and n.right is not None

    if op == Op.PRIM:
        if n.step is None:
            err("PRIM_NO_STEP", "prim node has no step")
    else:
        if n.step is not None:
            err("STEP_ON_NONPRIM", f"{op.value} node must not carry a step")

    if op != Op.ALT and (n.select is not None or n.cases is not None or n.default is not None):
        err("ALT_FIELDS_ON_NONALT", f"{op.value} node must not carry alt switch fields")

    if op in (Op.SEQ, Op.PAR):
        if not has_lr:
            err("MISSING_BRANCH", f"{op.value} requires both left and right")

    if op == Op.ALT:
        if n.cases is not None:
            if n.left is not None or n.right is not None:
                err("ALT_SWITCH_HAS_BINARY_BRANCH", "alt switch must not carry left/right branches")
            if n.pure is not None:
                err("ALT_SWITCH_HAS_PRED", "alt switch must not carry a binary predicate")
            if n.select is None:
                err("ALT_NO_SELECT", "alt switch requires a named pure selector")
            elif not is_registered(n.select):
                err("UNKNOWN_PURE", f"alt selector not registered: {n.select!r}")
            if not n.cases:
                err("ALT_NO_CASES", "alt switch requires at least one case")
            for key, child in n.cases.items():
                if not isinstance(key, str):
                    err("ALT_BAD_CASE_KEY", "alt switch case keys must be strings")
                if not isinstance(child, Node):
                    err("ALT_BAD_CASE", f"alt switch case {key!r} is not a flow")
        else:
            if not has_lr:
                err("MISSING_BRANCH", "alt requires both left and right")
            if n.select is not None:
                err("ALT_BINARY_HAS_SELECT", "binary alt must not carry a switch selector")
            if n.default is not None:
                err("ALT_BINARY_HAS_DEFAULT", "binary alt must not carry a switch default")
            if n.pure is None:
                err("ALT_NO_PRED", "alt requires a named pure predicate")
            elif not is_registered(n.pure):
                err("UNKNOWN_PURE", f"alt predicate not registered: {n.pure!r}")

    if op == Op.ARR:
        if n.pure is None:
            err("ARR_NO_PURE", "arr requires a named pure function (no inline closures)")
        elif not is_registered(n.pure):
            err("UNKNOWN_PURE", f"arr function not registered: {n.pure!r}")
        if (
            n.left is not None
            or n.right is not None
            or n.body is not None
            or n.cases is not None
            or n.default is not None
        ):
            err("ARR_HAS_CHILD", "arr is a leaf and must not have children")

    if op == Op.ITER_UP_TO:
        if n.body is None:
            err("ITER_NO_BODY", "iter_up_to requires a body")
        if n.bound is None or n.bound < 1:
            err("ITER_BAD_BOUND", "iter_up_to requires bound >= 1")
        if n.pure is not None and not is_registered(n.pure):
            err("UNKNOWN_PURE", f"convergence predicate not registered: {n.pure!r}")

    if op == Op.EVAL_PLAN:
        # A plan is either baked in (extracted/pre-validated) or produced at
        # runtime by `controller` (a planner brain). At least one must be present.
        if n.plan is None and n.controller is None:
            err("EVAL_NO_PLAN", "eval_plan requires a plan payload or a planner controller")
        if n.plan is not None:
            s = surface_shape(n.plan)
            if not shape_leq(s, Shape.FEEDBACK):
                err(
                    "EVAL_PLAN_TOO_RICH",
                    f"eval_plan.plan must be <= Feedback, got {s.value}",
                )

    if op == Op.APP:
        if n.controller is None:
            err("APP_NO_CONTROLLER", "app requires a controller ref")


def _check_call_and_ctx(n: Node, manifest: Optional[ToolManifest], out: list[Diagnostic]) -> None:
    step = n.step
    if isinstance(step, CallStep) and manifest is not None:
        if step.frozen_hash is None:
            out.append(Diagnostic("UNFROZEN_CALL", n.id, "call node was not frozen"))
        elif step.frozen_hash not in manifest:
            out.append(
                Diagnostic(
                    "MISSING_MANIFEST",
                    n.id,
                    f"call bound to {step.frozen_hash} absent from manifest",
                )
            )


def _ctx_of(n: Node) -> Optional[ContextPolicy]:
    step = n.step
    if isinstance(step, (CallStep, ThinkStep)):
        return step.ctx
    return None


def reads_whole_session(n: Node) -> bool:
    """True if any call/think leaf in ``n`` reads whole-session context."""
    for d in n.walk():
        ctx = _ctx_of(d)
        if ctx is not None and ctx.scope == ContextScope.WHOLE_SESSION:
            return True
    return False


def validate(flow: Node, manifest: Optional[ToolManifest] = None) -> list[Diagnostic]:
    """Validate a flow. Pass ``manifest`` (post-freeze) to enable schema and
    manifest-resolution checks; structural checks always run."""
    out: list[Diagnostic] = []

    # finite tree / no knots
    cycle = detect_cycles(flow)
    if cycle is not None:
        out.append(
            Diagnostic("CYCLE", cycle[-1], "flow has a cycle: " + " -> ".join(cycle))
        )
        return out  # don't traverse a cyclic graph further

    # unique ids
    for dup in collect_duplicate_ids(flow):
        out.append(
            Diagnostic(
                "DUP_ID",
                dup,
                f"node id {dup!r} appears more than once (build distinct instances)",
            )
        )

    for n in flow.walk():
        _check_structure(n, out)
        _check_call_and_ctx(n, manifest, out)

        # seq edge schema subtyping
        if n.op == Op.SEQ and n.left is not None and n.right is not None:
            reason = schema_incompatibility(
                _exit_schema(n.left, manifest), _entry_schema(n.right, manifest)
            )
            if reason:
                out.append(
                    Diagnostic("SEQ_TYPE", n.id, f"seq edge type mismatch: {reason}")
                )

        # ContextPolicy legality under par -> sequential degrade (warning)
        if n.op == Op.PAR and n.left is not None and n.right is not None:
            for side, label in ((n.left, "left"), (n.right, "right")):
                if reads_whole_session(side):
                    out.append(
                        Diagnostic(
                            "CTX_PAR_DEGRADED",
                            n.id,
                            f"par {label} branch reads whole session; "
                            "fan-out will be degraded to sequential",
                            severity="warning",
                        )
                    )

    return out
