"""Typed authoring wrappers over the core :class:`~composable_agents.ir.Node` IR.

``Flow`` is authoring-only: it carries Python type information while building a
program, elaborates to a ``Node``, and disappears before freeze. Composition
lowers through the same :mod:`composable_agents.dsl` helpers, including
``dsl.seq``'s left-fold, so the emitted IR is byte-identical to the string DSL
apart from provisional node ids.
"""

from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, TypeVar, overload

from . import dsl
from .derived import map_n
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


class FlowLike(Generic[In, Out]):
    """Anything that lowers to a Node and composes with >> : Flow and Tool."""

    __slots__ = ()

    def to_ir(self) -> Node:
        raise NotImplementedError

    def __rshift__(self, other: "FlowLike[Out, Next]") -> "Flow[In, Next]":
        """`X[I,M] >> Y[M,O] -> Flow[I,O]`; lowers via the dsl.seq left-fold."""
        return Flow(dsl.seq(self.to_ir(), other.to_ir()))


class Flow(FlowLike[In, Out]):
    """A typed authoring wrapper over a `Node`. Disappears before freeze."""

    __slots__ = ("_node",)

    def __init__(self, node: Node) -> None:
        self._node = node

    def to_ir(self) -> Node:
        """The underlying IR node (the only thing that is ever serialized)."""
        return self._node

    def __repr__(self) -> str:
        return f"Flow({self._node.op.value}#{self._node.id})"


@overload
def flow(x: FlowLike[In, Out]) -> Flow[In, Out]: ...


@overload
def flow(x: Node) -> Flow[Any, Any]: ...


def flow(x: FlowLike[Any, Any] | Node) -> Flow[Any, Any]:
    """Lift an IR `Node` or lowerable typed value into a `Flow`."""
    if isinstance(x, FlowLike):
        return Flow(x.to_ir())
    return Flow(x)


@overload
def seq(f0: FlowLike[_T0, _T1], /) -> Flow[_T0, _T1]: ...


@overload
def seq(f0: FlowLike[_T0, _T1], f1: FlowLike[_T1, _T2], /) -> Flow[_T0, _T2]: ...


@overload
def seq(
    f0: FlowLike[_T0, _T1],
    f1: FlowLike[_T1, _T2],
    f2: FlowLike[_T2, _T3],
    /,
) -> Flow[_T0, _T3]: ...


@overload
def seq(
    f0: FlowLike[_T0, _T1],
    f1: FlowLike[_T1, _T2],
    f2: FlowLike[_T2, _T3],
    f3: FlowLike[_T3, _T4],
    /,
) -> Flow[_T0, _T4]: ...


@overload
def seq(
    f0: FlowLike[_T0, _T1],
    f1: FlowLike[_T1, _T2],
    f2: FlowLike[_T2, _T3],
    f3: FlowLike[_T3, _T4],
    f4: FlowLike[_T4, _T5],
    /,
) -> Flow[_T0, _T5]: ...


@overload
def seq(
    f0: FlowLike[_T0, _T1],
    f1: FlowLike[_T1, _T2],
    f2: FlowLike[_T2, _T3],
    f3: FlowLike[_T3, _T4],
    f4: FlowLike[_T4, _T5],
    f5: FlowLike[_T5, _T6],
    /,
) -> Flow[_T0, _T6]: ...


@overload
def seq(
    f0: FlowLike[_T0, _T1],
    f1: FlowLike[_T1, _T2],
    f2: FlowLike[_T2, _T3],
    f3: FlowLike[_T3, _T4],
    f4: FlowLike[_T4, _T5],
    f5: FlowLike[_T5, _T6],
    f6: FlowLike[_T6, _T7],
    /,
) -> Flow[_T0, _T7]: ...


@overload
def seq(
    f0: FlowLike[_T0, _T1],
    f1: FlowLike[_T1, _T2],
    f2: FlowLike[_T2, _T3],
    f3: FlowLike[_T3, _T4],
    f4: FlowLike[_T4, _T5],
    f5: FlowLike[_T5, _T6],
    f6: FlowLike[_T6, _T7],
    f7: FlowLike[_T7, _T8],
    /,
) -> Flow[_T0, _T8]: ...


@overload
def seq(*flows: FlowLike[Any, Any]) -> Flow[Any, Any]: ...


def seq(*flows: FlowLike[Any, Any]) -> Flow[Any, Any]:
    if not flows:
        raise ValueError("seq needs at least one flow")
    return Flow(dsl.seq(*[f.to_ir() for f in flows]))


def par(
    branches: Sequence[FlowLike[In, Any]],
    *,
    join: Optional[str] = None,
) -> Flow[In, Any]:
    """Run branches concurrently on the same input.

    `join` names a registered pure reducer over the collected results. Output is
    honestly `Any` across that reduce boundary; re-type later with an explicit
    adapter.
    """
    nodes = [branch.to_ir() for branch in branches]
    if join is None:
        return Flow(dsl.par(*nodes))
    return Flow(map_n(*nodes, reducer=join))


def alt(pred: str, if_true: FlowLike[In, Out], if_false: FlowLike[In, Out]) -> Flow[In, Out]:
    """Binary branch on a registered pure predicate; both arms share I->O."""
    return Flow(dsl.alt(pred, if_true.to_ir(), if_false.to_ir()))
