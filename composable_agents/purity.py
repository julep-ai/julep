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

from typing import Callable

from .registry import DEFAULT_REGISTRY, PureEntry, PureFn, _source_hash as _registry_source_hash

_REGISTRY: dict[str, PureEntry] = DEFAULT_REGISTRY.pures


def _source_hash(fn: PureFn) -> str:
    return _registry_source_hash(fn)


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
