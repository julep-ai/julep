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

import hashlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable

PureFn = Callable[[Any], Any]


@dataclass(frozen=True)
class PureEntry:
    name: str
    fn: PureFn
    source_hash: str


_REGISTRY: dict[str, PureEntry] = {}


def _source_hash(fn: PureFn) -> str:
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        # e.g. defined in a REPL; fall back to qualname so it's at least stable
        src = f"{fn.__module__}.{getattr(fn, '__qualname__', fn.__name__)}"
    digest = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
    return f"pure:{digest}"


def pure(name: str) -> Callable[[PureFn], PureFn]:
    """Register a deterministic predicate/map under ``name``.

    Usage::

        @pure("route.is_long")
        def is_long(x):
            return len(x["text"]) > 1000
    """

    def deco(fn: PureFn) -> PureFn:
        register_pure(name, fn)
        return fn

    return deco


def register_pure(name: str, fn: PureFn) -> PureEntry:
    if name in _REGISTRY and _REGISTRY[name].fn is not fn:
        raise ValueError(f"pure name already registered to a different fn: {name!r}")
    entry = PureEntry(name=name, fn=fn, source_hash=_source_hash(fn))
    _REGISTRY[name] = entry
    return entry


def is_registered(name: str) -> bool:
    return name in _REGISTRY


def get_pure(name: str) -> PureFn:
    try:
        return _REGISTRY[name].fn
    except KeyError as e:
        raise KeyError(
            f"unknown pure {name!r}; register it with @pure({name!r}) on a worker"
        ) from e


def source_hash_of(name: str) -> str:
    return _REGISTRY[name].source_hash


def diff_pure_hashes(
    pinned: dict[str, str],
    registered: dict[str, str],
) -> list[dict[str, str | None]]:
    """Return changed or missing pure source hashes compared to a pinned artifact."""
    drift: list[dict[str, str | None]] = []
    for name in sorted(pinned):
        pinned_hash = pinned[name]
        actual_hash = registered.get(name)
        if actual_hash != pinned_hash:
            drift.append({"name": name, "pinned": pinned_hash, "actual": actual_hash})
    return drift


def registered_names() -> list[str]:
    return sorted(_REGISTRY)
