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
* ``arr.args``: static args are canonical JSON objects with identifier keys and
  no secret-shaped keys at any nesting level
* post-freeze: every ``call`` resolves to a manifest entry
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Optional, cast

from .contracts import ToolManifest, contract_allows_retry
from .ir import (
    CallStep,
    ContextPolicy,
    JSONSchema,
    Node,
    SourceSpan,
    ThinkStep,
    canonical_json,
    pure_display,
)
from .kinds import ContextScope, Effect, Op, Shape, shape_leq
from .purity import is_registered
from .shapes import surface_shape
from .transforms import collect_duplicate_ids, detect_cycles


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SECRET_KEY_RE = re.compile(
    r"token|secret|password|api_?key|credential|private_?key",
    re.IGNORECASE,
)


@dataclass
class Diagnostic:
    code: str
    node_id: str
    message: str
    severity: str = "error"  # "error" | "warning"
    hint: Optional[str] = None
    help_url: Optional[str] = None
    source: Optional[SourceSpan] = None


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
        return _entry_schema(cast(Node, n.left), manifest)
    if op == Op.ITER_UP_TO:
        return _entry_schema(cast(Node, n.body), manifest)
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
        return _exit_schema(cast(Node, n.right), manifest)
    if op == Op.ITER_UP_TO:
        return _exit_schema(cast(Node, n.body), manifest)
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

    if op != Op.ARR and n.args is not None:
        err("ARR_ARGS_ON_NONARR", f"{op.value} node must not carry arr static args")

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
            err(
                "UNKNOWN_PURE",
                f"arr function not registered: {pure_display(n.pure, n.args)!r}",
            )
        _check_arr_args(n, out)
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

    if op == Op.EACH:
        if n.body is None:
            err("EACH_NO_BODY", "each requires a body")
        if n.bound is not None and n.bound < 1:
            err("EACH_BAD_BOUND", "each max_parallel must be >= 1")
        if n.pure is not None and not is_registered(n.pure):
            err("UNKNOWN_PURE", f"each reducer not registered: {n.pure!r}")

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
        # Transcript scopes (agent-transcripts design): no implicit budget, no
        # implicit summarizer model — declaring either without its requirement
        # is a blocking diagnostic, never a silent fallback.
        if n.ctx is not None and n.ctx.scope in (
            ContextScope.WHOLE_SESSION,
            ContextScope.SUMMARY,
        ):
            if n.ctx.max_tokens is None:
                err(
                    "APP_CTX_NO_BUDGET",
                    f"app with {n.ctx.scope.value} context requires ctx.max_tokens; "
                    "there is no implicit transcript budget",
                )
            if n.ctx.scope == ContextScope.SUMMARY and n.summarizer is None:
                err(
                    "APP_SUMMARY_NO_SUMMARIZER",
                    "app with summary context requires a named summarizer brain "
                    "(summarizer=...); there is no implicit default model",
                )


def _check_arr_args(n: Node, out: list[Diagnostic]) -> None:
    args = n.args
    if args is None:
        return

    def err(code: str, msg: str) -> None:
        out.append(Diagnostic(code, n.id, msg))

    if not isinstance(args, dict):
        err("ARR_ARGS_NOT_OBJECT", "arr static args must be a JSON object")
        return

    if _check_json_value(args, "args", out, n.id):
        try:
            canonical_json(args)
        except TypeError as exc:
            err("ARR_ARGS_NOT_JSON", f"arr static args are not canonical JSON: {exc}")


def _check_json_value(
    value: Any,
    path: str,
    out: list[Diagnostic],
    node_id: str,
) -> bool:
    ok = True

    def err(code: str, msg: str) -> None:
        out.append(Diagnostic(code, node_id, msg))

    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or not _IDENTIFIER_RE.match(key):
                err(
                    "ARR_ARGS_BAD_KEY",
                    f"arr static arg key {path}.{key!r} must be a valid Python identifier",
                )
                ok = False
            elif _SECRET_KEY_RE.search(key):
                err(
                    "ARR_ARGS_SECRET",
                    f"arr static arg key {path}.{key} looks secret-shaped; use env/hands instead",
                )
                ok = False
            child_path = f"{path}.{key}" if isinstance(key, str) else f"{path}.<key>"
            if not _check_json_value(child, child_path, out, node_id):
                ok = False
        return ok

    if isinstance(value, list):
        for index, item in enumerate(value):
            if not _check_json_value(item, f"{path}[{index}]", out, node_id):
                ok = False
        return ok

    if value is None or isinstance(value, (str, bool, int)):
        return True

    if isinstance(value, float):
        if math.isfinite(value):
            return True
        err("ARR_ARGS_NOT_JSON", f"arr static arg {path} must be a finite JSON number")
        return False

    err(
        "ARR_ARGS_NOT_JSON",
        f"arr static arg {path} has non-JSON value type {type(value).__name__}",
    )
    return False


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
        else:
            tool = manifest[step.frozen_hash]
            if (
                n.ann is not None
                and n.ann.max_attempts is not None
                and n.ann.max_attempts > 1
                and tool.contract.effect == Effect.DANGEROUS
                and not contract_allows_retry(tool.contract)
            ):
                out.append(
                    Diagnostic(
                        "RETRY_NON_IDEMPOTENT_DANGEROUS",
                        n.id,
                        "explicit max_attempts > 1 on a non-idempotent dangerous tool "
                        "is not allowed",
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

        # Same legality rule for dynamic fan-out: a whole-session body can't
        # run per-item concurrently without racing on the transcript.
        if n.op == Op.EACH and n.body is not None and reads_whole_session(n.body):
            out.append(
                Diagnostic(
                    "CTX_EACH_DEGRADED",
                    n.id,
                    "each body reads whole session; per-item fan-out will be "
                    "degraded to sequential",
                    severity="warning",
                )
            )

    return out
