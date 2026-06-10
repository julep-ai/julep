"""Explicit registries for named brains and pure functions.

The module-level :data:`DEFAULT_REGISTRY` backs the historical global shims in
``dotctx`` and ``purity``. Tests and local harnesses can instantiate
:class:`Registry` directly when they need isolation without changing decorator
ergonomics for the default process-global path.
"""

from __future__ import annotations

import hashlib
import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from .dotctx import Brain

PureFn = Callable[[Any], Any]


@dataclass(frozen=True)
class PureEntry:
    name: str
    fn: PureFn
    source_hash: str


@dataclass(frozen=True)
class RendererEntry:
    name: str
    fn: Callable[[Mapping[str, Any]], str]
    source_hash: str


@dataclass(frozen=True)
class ToolSchemaExpectation:
    """The prompt-side tool contract a dotctx package was written against.

    Recorded at load (``tools.pyi``); compared by canonical hash against the
    served schema when freeze resolves the tool (``TOOL_SCHEMA_DRIFT``).
    """

    key: str                        # toolref key: native name or "server/tool"
    input_schema: dict[str, Any]    # expected JSON Schema for the tool input
    ctx_path: str                   # the .ctx package that recorded it


def _text_hash(src: str) -> str:
    digest = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
    return f"pure:{digest}"


def _source_hash(fn: PureFn) -> str:
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        # e.g. defined in a REPL; fall back to qualname so it's at least stable
        src = f"{fn.__module__}.{getattr(fn, '__qualname__', fn.__name__)}"
    return _text_hash(src)


class Registry:
    """An explicit registry for named brains and deterministic pure functions."""

    def __init__(self) -> None:
        self.brains: dict[str, Brain] = {}
        self.pures: dict[str, PureEntry] = {}
        self.renderers: dict[str, RendererEntry] = {}
        self.tool_expectations: dict[str, ToolSchemaExpectation] = {}

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

    def register_renderer(
        self,
        name: str,
        fn: Callable[[Mapping[str, Any]], str],
        *,
        source: Optional[str] = None,
    ) -> RendererEntry:
        """Register a renderer. ``source`` overrides the hashed text for
        renderers whose behavior is data (e.g. a compiled template): hash the
        template content, not the shared closure source."""
        if name in self.renderers and self.renderers[name].fn is not fn:
            raise ValueError(f"renderer name already registered to a different fn: {name!r}")
        hashed = _text_hash(source) if source is not None else _source_hash(fn)
        entry = RendererEntry(
            name=name, fn=fn, source_hash=hashed.replace("pure:", "renderer:", 1)
        )
        self.renderers[name] = entry
        return entry

    def get_renderer(self, name: str) -> Callable[[Mapping[str, Any]], str]:
        try:
            return self.renderers[name].fn
        except KeyError as e:
            raise KeyError(f"unknown renderer {name!r}; register it with @renderer({name!r})") from e

    def renderer_source_hash_of(self, name: str) -> str:
        return self.renderers[name].source_hash

    def register_tool_expectation(self, exp: ToolSchemaExpectation) -> ToolSchemaExpectation:
        existing = self.tool_expectations.get(exp.key)
        if existing is not None and existing.input_schema != exp.input_schema:
            raise ValueError(
                f"conflicting expected schemas for tool {exp.key!r}: "
                f"{existing.ctx_path!r} vs {exp.ctx_path!r}"
            )
        self.tool_expectations[exp.key] = exp
        return exp

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
