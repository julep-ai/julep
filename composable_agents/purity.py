"""The named ``Pure`` registry (blueprint §1, "no inline closures").

``arr`` and ``alt`` carry a *name*, never a closure. The workflow looks the
function up by name on the worker; replay verifies the function's source hash
hasn't drifted. Registering is the only sanctioned way to get a name into
deployed IR, which is why the validator rejects any ``arr``/``alt`` whose ``pure``
field doesn't resolve here.

Determinism contract: a registered function must depend only on its input
(no clocks, no IO, no globals). It runs *inside the Temporal workflow*, so a
non-deterministic predicate will desync replay. Keep them total and pure.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import Any, Callable, overload

from . import dsl
from .typed import FlowLike
from .ir import Node
from .registry import DEFAULT_REGISTRY, PureEntry, PureFn, _source_hash as _registry_source_hash

_REGISTRY: dict[str, PureEntry] = DEFAULT_REGISTRY.pures


def _source_hash(fn: PureFn) -> str:
    return _registry_source_hash(fn)


class Pure(FlowLike[Any, Any]):
    """A registered pure function as a first-class authoring object."""

    fn: PureFn
    name: str

    def __init__(self, name: str, fn: PureFn) -> None:
        self.name = name
        self.fn = fn
        update_wrapper(self, fn)

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        from .define import apply_if_authoring

        authored = apply_if_authoring(self, (value,), kwargs)
        if authored is not NotImplemented:
            return authored
        return self.fn(value, **kwargs)

    def to_ir(self) -> Node:
        return dsl.arr(self.name)


@overload
def pure(fn: PureFn, /) -> Pure: ...


@overload
def pure(name: str, /) -> Callable[[PureFn], Pure]: ...


def pure(name: str | PureFn, /) -> Pure | Callable[[PureFn], Pure]:
    """Register a deterministic predicate/map under ``name``.

    Usage::

        @pure
        def normalize(x):
            return x

        @pure("route.is_long")
        def is_long(x):
            return len(x["text"]) > 1000
    """

    if not isinstance(name, str):
        register_pure(name.__name__, name)
        return Pure(name.__name__, name)

    def deco(fn: PureFn) -> Pure:
        register_pure(name, fn)
        return Pure(name, fn)

    return deco


def register_pure(name: str, fn: PureFn) -> PureEntry:
    return DEFAULT_REGISTRY.register_pure(name, fn)


def is_registered(name: str) -> bool:
    return DEFAULT_REGISTRY.is_registered(name)


def get_pure(name: str) -> PureFn:
    return DEFAULT_REGISTRY.get_pure(name)


def source_hash_of(name: str) -> str:
    return DEFAULT_REGISTRY.source_hash_of(name)


def diff_pure_hashes(
    pinned: dict[str, str],
    registered: dict[str, str],
) -> list[dict[str, str | None]]:
    """Return changed or missing pure source hashes compared to a pinned artifact."""
    return DEFAULT_REGISTRY.diff_pure_hashes(pinned, registered)


def registered_names() -> list[str]:
    return DEFAULT_REGISTRY.registered_names()
