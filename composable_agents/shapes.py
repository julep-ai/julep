"""Shape analysis (blueprint §4, the join-semilattice).

Two reads of the same tree:

* :func:`surface_shape` — what the *parent's* scheduler sees. A ``Sub`` is
  opaque: from the surface it is one scheduled, checkpointed unit, so it costs a
  ``Pipeline``. This is what decides whether the parent can race a branch.
* :func:`closed_shape` — what *budgeting and admission* see. A ``Sub`` reveals
  its ``contract.shape`` (without loading the child), so a child that is secretly
  an ``Agent`` still charges Agent rent against the budget.

Both are pure structural folds: composition is the join of children, with a
per-operator floor (``par`` >= Dataflow, ``alt`` >= Branching, ``iter_up_to`` >=
Feedback, ``eval_plan`` == Staged, ``app`` == Agent). Because the node tree is
finite (recursion only happens at *evaluation* time inside the looping ops),
this terminates and is decidable.
"""

from __future__ import annotations

from typing import cast

from .ir import CallStep, Node, SubStep, ThinkStep
from .kinds import Op, Shape, shape_join

_SURFACE = "surface"
_CLOSED = "closed"


def _shape(n: Node, mode: str) -> Shape:
    op = n.op

    if op in (Op.IDENT, Op.ARR):
        return Shape.PIPELINE

    if op == Op.PRIM:
        step = n.step
        if step is None:
            return Shape.PIPELINE
        if isinstance(step, (CallStep, ThinkStep)):
            return Shape.PIPELINE
        if isinstance(step, SubStep):
            # Surface: opaque, a single scheduled unit -> Pipeline.
            # Closed: charge the declared contract shape.
            return Shape.PIPELINE if mode == _SURFACE else step.contract.shape
        return Shape.PIPELINE

    if op == Op.SEQ:
        return shape_join(_shape(cast(Node, n.left), mode), _shape(cast(Node, n.right), mode))

    if op == Op.PAR:
        # Concurrency is a structural property: at least Dataflow regardless of
        # how trivial the branches are.
        return shape_join(
            Shape.DATAFLOW,
            _shape(cast(Node, n.left), mode),
            _shape(cast(Node, n.right), mode),
        )

    if op == Op.EACH:
        # Dynamic fan-out over a runtime list: concurrency is structural, same
        # floor as `par`; the per-item body raises the join like any branch.
        return shape_join(Shape.DATAFLOW, _shape(cast(Node, n.body), mode))

    if op == Op.ALT:
        # Two or more possible continuations -> at least Branching.
        if n.cases is not None:
            branches = [_shape(n.cases[k], mode) for k in sorted(n.cases)]
            if n.default is not None:
                branches.append(_shape(n.default, mode))
            return shape_join(Shape.BRANCHING, *branches)
        return shape_join(
            Shape.BRANCHING,
            _shape(cast(Node, n.left), mode),
            _shape(cast(Node, n.right), mode),
        )

    if op == Op.ITER_UP_TO:
        # A bounded loop owns its continuation across rounds -> at least Feedback.
        return shape_join(Shape.FEEDBACK, _shape(cast(Node, n.body), mode))

    if op == Op.EVAL_PLAN:
        # Staging model-generated structure is Staged. The plan payload is
        # separately constrained to <= Feedback by the validator.
        return Shape.STAGED

    if op == Op.APP:
        # Open-ended controller loop -> top of the lattice.
        return Shape.AGENT

    raise ValueError(f"unhandled op in shape analysis: {op!r}")


def surface_shape(n: Node) -> Shape:
    """Shape as the parent scheduler sees it (Sub opaque)."""
    return _shape(n, _SURFACE)


def closed_shape(n: Node) -> Shape:
    """Shape for budgeting / admission (Sub reveals its contract shape)."""
    return _shape(n, _CLOSED)
