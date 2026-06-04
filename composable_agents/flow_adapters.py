"""Authoring-only adapters and Any-edge reporting for typed flows.

``as_type`` and ``expect`` re-type a flow edge for Python authors, but they
lower to ``dsl.ident()``: no runtime coercion is performed and no validation is
inserted. The value that crosses the edge is passed through unchanged.

``any_edges`` is the typed-composable-flow §13 Any-edge report fragment. It is
structural and best-effort, emits no IR, and reports inherent agent/LLM/JSON
boundaries visible in the existing IR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar

from . import dsl
from .flow import Flow
from .ir import Node, ThinkStep
from .kinds import Op

In = TypeVar("In")
T = TypeVar("T")


def as_type(t: type[T]) -> Flow[Any, T]:
    """Authoring-only cast that lowers to ``dsl.ident()``.

    The ``t`` argument is consumed purely for its type. Its value is never
    inspected, no validation is inserted, and the runtime value is passed
    through unchanged.

    Example:
        ``agent >> as_type(Ticket) >> classify``
    """
    return Flow(dsl.ident())


def expect(f: Flow[In, Any], t: type[T]) -> Flow[In, T]:
    """Retype the output of ``f`` to ``T``.

    This is the free-function spelling of a hypothetical ``f.expect(T)`` method,
    which would require editing ``flow.py``. It re-types the output of ``f`` to
    ``T`` and lowers to ``seq(f, ident)``.

    Example:
        ``expect(inbox, Triage) >> route``
    """
    return f >> as_type(t)


@dataclass(frozen=True)
class AnyEdge:
    """A structural Any-boundary edge surfaced by `any_edges`."""

    node_id: str
    op: str
    reason: str


def any_edges(f: Flow[Any, Any]) -> list[AnyEdge]:
    """Report structural agent/LLM/JSON boundaries in pre-order.

    ``Flow``'s ``In``/``Out`` TypeVars are erased at runtime because Python
    generics carry no runtime type information. ``any_edges`` therefore cannot
    read the static type parameters; it approximates the "Any edge" signal
    structurally from IR ops.

    Because ``as_type`` and ``expect`` lower to a bare ``ident`` node, the IR is
    indistinguishable from any other identity pass-through. This reporter cannot
    tell whether a downstream adapter has already re-typed (tamed) a boundary, so
    it reports every structural boundary and leaves the final "is this edge still
    ``Any``?" verdict to the type checker. It also does not descend into ``APP``
    inline ``tools``/``subflows`` config.
    """
    root: Node = f.to_ir()
    out: list[AnyEdge] = []
    for node in root.walk():
        reason: str | None = None
        if node.op is Op.APP:
            reason = "app (agent/LLM controller loop) — output is model-generated (Any)"
        elif node.op is Op.EVAL_PLAN:
            reason = "eval_plan (LLM-planned staging) — output is Any"
        elif node.op is Op.PRIM and isinstance(node.step, ThinkStep):
            reason = "think (single model call) — output is Any"

        if reason is not None:
            out.append(AnyEdge(node.id, node.op.value, reason))
    return out


__all__ = ["AnyEdge", "any_edges", "as_type", "expect"]
