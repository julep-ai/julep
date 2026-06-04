"""Typed authoring wrappers over the core :class:`~composable_agents.ir.Node` IR.

``Flow`` is authoring-only: it carries Python type information while building a
program, elaborates to a ``Node``, and disappears before freeze. Composition
lowers through the same :mod:`composable_agents.dsl` helpers, including
``dsl.seq``'s left-fold, so the emitted IR is byte-identical to the string DSL
apart from provisional node ids.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar, overload

from . import dsl
from .ir import Node

In = TypeVar("In")
Out = TypeVar("Out")
Next = TypeVar("Next")

_T0 = TypeVar("_T0")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T4 = TypeVar("_T4")
_T5 = TypeVar("_T5")
_T6 = TypeVar("_T6")
_T7 = TypeVar("_T7")
_T8 = TypeVar("_T8")


class Flow(Generic[In, Out]):
    """A typed authoring wrapper over a `Node`. Disappears before freeze."""

    __slots__ = ("_node",)

    def __init__(self, node: Node) -> None:
        self._node = node

    def to_ir(self) -> Node:
        """The underlying IR node (the only thing that is ever serialized)."""
        return self._node

    def __rshift__(self, other: "Flow[Out, Next]") -> "Flow[In, Next]":
        """`Flow[I,M] >> Flow[M,O] -> Flow[I,O]`; lowers via the dsl left-fold."""
        return Flow(dsl.seq(self._node, other._node))

    def __repr__(self) -> str:
        return f"Flow({self._node.op.value}#{self._node.id})"


def flow(node: Node) -> Flow[Any, Any]:
    """Lift an existing IR `Node` into an (untyped) `Flow`."""
    return Flow(node)


@overload
def seq(f0: Flow[_T0, _T1], /) -> Flow[_T0, _T1]: ...


@overload
def seq(f0: Flow[_T0, _T1], f1: Flow[_T1, _T2], /) -> Flow[_T0, _T2]: ...


@overload
def seq(
    f0: Flow[_T0, _T1],
    f1: Flow[_T1, _T2],
    f2: Flow[_T2, _T3],
    /,
) -> Flow[_T0, _T3]: ...


@overload
def seq(
    f0: Flow[_T0, _T1],
    f1: Flow[_T1, _T2],
    f2: Flow[_T2, _T3],
    f3: Flow[_T3, _T4],
    /,
) -> Flow[_T0, _T4]: ...


@overload
def seq(
    f0: Flow[_T0, _T1],
    f1: Flow[_T1, _T2],
    f2: Flow[_T2, _T3],
    f3: Flow[_T3, _T4],
    f4: Flow[_T4, _T5],
    /,
) -> Flow[_T0, _T5]: ...


@overload
def seq(
    f0: Flow[_T0, _T1],
    f1: Flow[_T1, _T2],
    f2: Flow[_T2, _T3],
    f3: Flow[_T3, _T4],
    f4: Flow[_T4, _T5],
    f5: Flow[_T5, _T6],
    /,
) -> Flow[_T0, _T6]: ...


@overload
def seq(
    f0: Flow[_T0, _T1],
    f1: Flow[_T1, _T2],
    f2: Flow[_T2, _T3],
    f3: Flow[_T3, _T4],
    f4: Flow[_T4, _T5],
    f5: Flow[_T5, _T6],
    f6: Flow[_T6, _T7],
    /,
) -> Flow[_T0, _T7]: ...


@overload
def seq(
    f0: Flow[_T0, _T1],
    f1: Flow[_T1, _T2],
    f2: Flow[_T2, _T3],
    f3: Flow[_T3, _T4],
    f4: Flow[_T4, _T5],
    f5: Flow[_T5, _T6],
    f6: Flow[_T6, _T7],
    f7: Flow[_T7, _T8],
    /,
) -> Flow[_T0, _T8]: ...


@overload
def seq(*flows: Flow[Any, Any]) -> Flow[Any, Any]: ...


def seq(*flows: Flow[Any, Any]) -> Flow[Any, Any]:
    if not flows:
        raise ValueError("seq needs at least one flow")
    return Flow(dsl.seq(*[f.to_ir() for f in flows]))
