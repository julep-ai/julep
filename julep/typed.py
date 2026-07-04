"""Typed authoring wrappers over the core :class:`~julep.ir.Node` IR.

This module was renamed from the old typed ``flow`` module after the
package-root ``flow`` name became the public ``@flow`` decorator.

``Flow`` is authoring-only: it carries Python type information while building a
program, elaborates to a ``Node``, and disappears before freeze. Composition
lowers through the same :mod:`julep.dsl` helpers, including
``dsl.seq``'s left-fold, so the emitted IR is byte-identical to the string DSL
apart from provisional node ids.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Optional, Sequence, TypeVar, overload

from . import dsl
from .flow_registry import register_flow
from .ir import Node, canonical_json
from .transforms import normalize_ids

if TYPE_CHECKING:
    from .purity import Pure

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


def derive_local_name(node: Node) -> str:
    """A deterministic content-hash local name for an anonymous flow.

    This is for debug/inline use only; it is not a durable ref. Provisional node
    ids are normalized first.
    """
    normalized = normalize_ids(Node.from_json(node.to_json()))
    digest = hashlib.sha256(
        canonical_json(normalized.to_json()).encode("utf-8")
    ).hexdigest()[:8]
    return f"flow-{digest}"


class FlowLike(Generic[In, Out]):
    """Anything that lowers to a Node and composes with >> : Flow and Tool."""

    __slots__ = ()

    def to_ir(self) -> Node:
        raise NotImplementedError

    def _durable_ref(self) -> Optional[str]:
        return None

    def __rshift__(self, other: "FlowLike[Out, Next]") -> "Flow[In, Next]":
        """`X[I,M] >> Y[M,O] -> Flow[I,O]`; lowers via the dsl.seq left-fold."""
        return Flow(dsl.seq(self.to_ir(), other.to_ir()))

    def as_sub(self, queue: Optional[str] = None) -> "SplitCapability":
        """Promote a named flow/agent to its own split deployment unit."""
        ref = self._durable_ref()
        if ref is None:
            raise ValueError("split requires a durable ref: call .named(ref) first")
        return SplitCapability(ref=ref, target=self, queue=queue)

    def named(self, ref: str) -> "Flow[In, Out]":
        """Mint a durable ref and return a Flow carrying it."""
        register_flow(ref, self)
        return Flow(self.to_ir(), name=ref)

    def renamed(self, ref: str) -> "Flow[In, Out]":
        """Reassert identity intentionally, replacing any existing flow ref."""
        register_flow(ref, self, replace=True)
        return Flow(self.to_ir(), name=ref)


class Flow(FlowLike[In, Out]):
    """A typed authoring wrapper over a `Node`. Disappears before freeze."""

    __slots__ = ("_node", "_name")

    def __init__(self, node: Node, name: Optional[str] = None) -> None:
        self._node = node
        self._name = name

    def to_ir(self) -> Node:
        """The underlying IR node (the only thing that is ever serialized)."""
        return self._node

    def _durable_ref(self) -> Optional[str]:
        return self._name

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def local_name(self) -> str:
        return derive_local_name(self._node)

    def __repr__(self) -> str:
        return f"Flow({self._node.op.value}#{self._node.id})"


@dataclass(frozen=True)
class SplitCapability:
    """A named flow/agent marked for per-component split deployment."""

    ref: str
    target: FlowLike[Any, Any]
    queue: Optional[str] = None


def _pure_name(pure: str | Pure) -> str:
    if isinstance(pure, str):
        return pure
    return pure.name


@overload
def as_flow(x: FlowLike[In, Out]) -> Flow[In, Out]: ...


@overload
def as_flow(x: Node) -> Flow[Any, Any]: ...


def as_flow(x: FlowLike[Any, Any] | Node) -> Flow[Any, Any]:
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
    join: str | Pure | None = None,
) -> Flow[In, Any]:
    """Run branches concurrently on the same input.

    `join` names a registered pure reducer over the collected results. Output is
    honestly `Any` across that reduce boundary; re-type later with an explicit
    adapter.
    """
    nodes = [branch.to_ir() for branch in branches]
    if join is None:
        return Flow(dsl.par(*nodes))
    from .derived import map_n

    return Flow(map_n(*nodes, reducer=_pure_name(join)))


def alt(pred: str | Pure, if_true: FlowLike[In, Out], if_false: FlowLike[In, Out]) -> Flow[In, Out]:
    """Binary branch on a registered pure predicate; both arms share I->O."""
    return Flow(dsl.alt(_pure_name(pred), if_true.to_ir(), if_false.to_ir()))


@overload
def each(body: FlowLike[In, Out], *, max_parallel: Optional[int] = None) -> Flow[Sequence[In], list[Out]]: ...


@overload
def each(
    body: FlowLike[In, Out],
    *,
    max_parallel: Optional[int] = None,
    reducer: str | Pure,
) -> Flow[Sequence[In], Any]: ...


def each(
    body: FlowLike[In, Any],
    *,
    max_parallel: Optional[int] = None,
    reducer: str | Pure | None = None,
) -> Flow[Sequence[In], Any]:
    """Run ``body`` once per input-list element, collecting outputs in order.

    The typed face of :func:`julep.dsl.each`. ``reducer`` names a
    registered pure folded over the collected list; like ``par``'s ``join``, the
    output is honestly ``Any`` across that reduce boundary.
    """
    reducer_name = None if reducer is None else _pure_name(reducer)
    return Flow(dsl.each(body.to_ir(), max_parallel=max_parallel, reducer=reducer_name))
