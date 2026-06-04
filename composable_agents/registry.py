"""Explicit registries for named brains and pure functions.

The module-level :data:`DEFAULT_REGISTRY` backs the historical global shims in
``dotctx`` and ``purity``. Tests and local harnesses can instantiate
:class:`Registry` directly when they need isolation without changing decorator
ergonomics for the default process-global path.
"""

from __future__ import annotations

import hashlib
import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .dotctx import Brain

PureFn = Callable[[Any], Any]


@dataclass(frozen=True)
class PureEntry:
    name: str
    fn: PureFn
    source_hash: str


def _source_hash(fn: PureFn) -> str:
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        # e.g. defined in a REPL; fall back to qualname so it's at least stable
        src = f"{fn.__module__}.{getattr(fn, '__qualname__', fn.__name__)}"
    digest = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
    return f"pure:{digest}"


class Registry:
    """An explicit registry for named brains and deterministic pure functions."""

    def __init__(self) -> None:
        self.brains: dict[str, Brain] = {}
        self.pures: dict[str, PureEntry] = {}

    def register_brain(self, brain: Brain) -> Brain:
        if brain.name in self.brains and self.brains[brain.name] != brain:
            raise ValueError(f"brain {brain.name!r} already registered with a different config")
        self.brains[brain.name] = brain
        return brain

    def get_brain(self, name: str) -> Brain:
        try:
            return self.brains[name]
        except KeyError as e:
            raise KeyError(f"unknown brain {name!r}; load its dotctx with load_dotctx()") from e

    def list_brains(self) -> list[str]:
        return sorted(self.brains)

    def register_pure(self, name: str, fn: PureFn) -> PureEntry:
        if name in self.pures and self.pures[name].fn is not fn:
            raise ValueError(f"pure name already registered to a different fn: {name!r}")
        entry = PureEntry(name=name, fn=fn, source_hash=_source_hash(fn))
        self.pures[name] = entry
        return entry

    def get_pure(self, name: str) -> PureFn:
        try:
            return self.pures[name].fn
        except KeyError as e:
            raise KeyError(
                f"unknown pure {name!r}; register it with @pure({name!r}) on a worker"
            ) from e

    def is_registered(self, name: str) -> bool:
        return name in self.pures

    def source_hash_of(self, name: str) -> str:
        return self.pures[name].source_hash

    def diff_pure_hashes(
        self,
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

    def registered_names(self) -> list[str]:
        return sorted(self.pures)


DEFAULT_REGISTRY = Registry()
