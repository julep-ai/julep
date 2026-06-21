"""Explicit registries for named brains and pure functions.

The module-level :data:`DEFAULT_REGISTRY` backs the historical global shims in
``dotctx`` and ``purity``. Tests and local harnesses can instantiate
:class:`Registry` directly when they need isolation without changing decorator
ergonomics for the default process-global path.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Callable, Optional

from .deps import parse_pep723

if TYPE_CHECKING:
    from .dotctx import Brain

PureFn = Callable[..., Any]


def _wasm_source_only(*_args: object, **_kwargs: object) -> object:
    """The ``fn`` placeholder for a source-only (bundle-sourced) pure.

    Bundle source is NEVER exec'd on the host at registration: source-only pures
    execute through their selected runtime tier (via :meth:`Registry.get_pure`).
    This sentinel keeps ``PureEntry.fn`` populated without creating a host fn
    object; calling it is a programming error, never a real execution path.
    """
    raise RuntimeError(
        "source-only pure has no host-callable fn; it executes only through "
        "its selected runtime tier via get_pure"
    )


def _pure_decorator_name(source: str, name: str) -> bool:
    """Validate the ``@pure(<name-literal>)`` contract by static analysis.

    Parses ``source`` with :mod:`ast` (no execution) and returns ``True`` iff a
    top-level ``def`` carries a ``@pure("<name>")`` decorator whose string-literal
    argument equals ``name``. This is how bundle source is admitted without ever
    exec'ing its module-level code on the host.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            target = decorator.func
            if not (isinstance(target, ast.Name) and target.id == "pure"):
                continue
            if len(decorator.args) != 1 or decorator.keywords:
                continue
            arg = decorator.args[0]
            if isinstance(arg, ast.Constant) and arg.value == name:
                return True
    return False


@dataclass(frozen=True)
class PureEntry:
    name: str
    fn: PureFn
    source_hash: str
    executor: str = "native"
    source: str | None = None
    deps: tuple[str, ...] = ()
    requires_python: str | None = None
    env_hash: str | None = None


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

    # FIXME(P4-2/P4-6): inspect.getsource(fn) drops a module-top `# /// script` block
    # (the idiomatic PEP 723 placement) => a dep-declaring baked pure registers as no-dep
    # and `import <dep>` fails OPEN late in wasm. Reject pures that import an undeclared
    # third-party module, or support module-top metadata. See TODOS.md (P4 follow-ups).
    def register_pure(self, name: str, fn: PureFn) -> PureEntry:
        if name in self.pures and self.pures[name].fn is not fn:
            raise ValueError(f"pure name already registered to a different fn: {name!r}")
        deps: tuple[str, ...] = ()
        requires_python: str | None = None
        try:
            source = inspect.getsource(fn)
        except (OSError, TypeError):
            pass
        else:
            deps, requires_python = parse_pep723(source)
        entry = PureEntry(
            name=name,
            fn=fn,
            source_hash=_source_hash(fn),
            executor="native",
            source=None,
            deps=deps,
            requires_python=requires_python,
        )
        self.pures[name] = entry
        return entry

    def register_pure_from_source(
        self,
        name: str,
        source: str,
        *,
        tier: str = "wasm",
    ) -> PureEntry:
        """Register a bundle-sourced pure as the wasm tier WITHOUT host execution.

        The bundle's shipped source is the body of an untrusted (if signed) pure:
        it must run fail-closed through its selected tier, never directly in the
        host process. So we do not ``exec`` it here. We validate the
        ``@pure(name)`` contract by static analysis (:func:`_pure_decorator_name`),
        pin the source text on a source-only :class:`PureEntry`, and leave actual
        execution to :meth:`get_pure`. ``PureEntry.fn`` is set to the
        :func:`_wasm_source_only` sentinel: no host fn object is ever created.
        """
        if tier not in {"wasm", "native_venv"}:
            raise ValueError(f"unsupported pure source tier: {tier!r}")
        expected_hash = _text_hash(source)
        existing = self.pures.get(name)
        if existing is not None:
            if existing.source_hash != expected_hash:
                raise ValueError(
                    f"bundled source for pure {name!r} disagrees with baked registration: "
                    f"{existing.source_hash} != {expected_hash}"
                )
            # Same hash. Only a TRUE no-op when the entry is already in the
            # requested source tier: an equal-hash baked (native) entry must still
            # be PROMOTED to the bundle-requested tier so a bundle-sourced pure
            # never escapes policy just because the same source is baked into the
            # worker. (std.* is forbidden at the resolution boundary, so it never
            # reaches here; never overwrite.)
            if existing.executor == tier:
                return existing
            if name.startswith("std."):
                raise ValueError(
                    f"refusing to register std pure {name!r} from bundle source; "
                    "std pures stay baked/native"
                )
            # Fall through: replace the equal-hash entry with the requested tier.

        # Preserve the historical local invariant that the shipped text ends in a
        # newline (the published sourceHash is computed over that canonical text);
        # surface it as a hash mismatch so the wording matches existing callers.
        if not source.endswith("\n"):
            raise ValueError(
                f"source hash mismatch for pure {name!r}: shipped source must end "
                "with a trailing newline to match its pinned sourceHash"
            )

        if not _pure_decorator_name(source, name):
            raise ValueError(f"source did not register requested pure {name!r}")

        deps, requires_python = parse_pep723(source)
        entry = PureEntry(
            name=name,
            fn=_wasm_source_only,
            source_hash=expected_hash,
            executor=tier,
            source=source,
            deps=deps,
            requires_python=requires_python,
        )
        self.pures[name] = entry
        return entry

    def get_pure(self, name: str) -> PureFn:
        try:
            entry = self.pures[name]
        except KeyError as e:
            raise KeyError(
                f"unknown pure {name!r}; register it with @pure({name!r}) on a worker"
            ) from e
        if entry.executor == "wasm":
            source = entry.source
            if source is None:
                return entry.fn
            source_text = source
            from .execution.wasm_executor import get_wasm_executor

            def wasm_bound(value: Any, **kwargs: Any) -> Any:
                return get_wasm_executor().run(
                    name,
                    source_text,
                    value,
                    kwargs,
                    env_hash=entry.env_hash,
                )

            return wasm_bound
        if entry.executor == "native_venv":
            source = entry.source
            if source is None:
                return entry.fn
            source_text = source
            from .execution.native_venv_executor import get_native_venv_executor

            def native_venv_bound(value: Any, **kwargs: Any) -> Any:
                return get_native_venv_executor().run(
                    name,
                    source_text,
                    value,
                    kwargs,
                    deps=entry.deps,
                    requires_python=entry.requires_python,
                )

            return native_venv_bound
        return entry.fn

    def set_pure_env_hash(self, name: str, env_hash: str) -> None:
        try:
            entry = self.pures[name]
        except KeyError as e:
            raise KeyError(f"unknown pure {name!r}; cannot set envHash") from e
        if entry.executor != "wasm":
            raise ValueError(f"pure {name!r} is not wasm-tier; cannot set envHash")
        self.pures[name] = replace(entry, env_hash=env_hash)

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
