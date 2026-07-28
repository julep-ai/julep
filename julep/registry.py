"""Explicit registries for named reasoners and pure functions.

The module-level :data:`DEFAULT_REGISTRY` backs the historical global shims in
``dotctx`` and ``purity``. Tests and local harnesses can instantiate
:class:`Registry` directly when they need isolation without changing decorator
ergonomics for the default process-global path.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from functools import lru_cache
from importlib import metadata
from typing import TYPE_CHECKING, Any, Callable, Optional

from .deps import parse_pep723
from .skills import Skill, skill_key

if TYPE_CHECKING:
    from .dotctx import Reasoner

PureFn = Callable[..., Any]
MAX_BUNDLE_PURE_SOURCE_BYTES = 256 * 1024

# Keep admission tied to the Python 3.14 stdlib embedded in executor.wasm, not
# to whichever host Python happens to validate the bundle. This is the guest's
# sys.stdlib_module_names captured when the vendored component was built.
_WASM_GUEST_STDLIB_MODULES = frozenset(
    """
    __future__ _abc _aix_support _android_support _apple_support _ast _ast_unparse
    _asyncio _bisect _blake2 _bz2 _codecs _codecs_cn _codecs_hk _codecs_iso2022
    _codecs_jp _codecs_kr _codecs_tw _collections _collections_abc _colorize
    _compat_pickle _contextvars _csv _ctypes _curses _curses_panel _datetime _dbm
    _decimal _elementtree _frozen_importlib _frozen_importlib_external _functools
    _gdbm _hashlib _heapq _hmac _imp _interpchannels _interpqueues _interpreters _io
    _ios_support _json _locale _lsprof _lzma _markupbase _md5 _multibytecodec
    _multiprocessing _opcode _opcode_metadata _operator _osx_support _overlapped
    _pickle _posixshmem _posixsubprocess _py_abc _py_warnings _pydatetime _pydecimal
    _pyio _pylong _pyrepl _queue _random _remote_debugging _scproxy _sha1 _sha2
    _sha3 _signal _sitebuiltins _socket _sqlite3 _sre _ssl _stat _statistics _string
    _strptime _struct _suggestions _symtable _sysconfig _thread _threading_local
    _tkinter _tokenize _tracemalloc _types _typing _uuid _warnings _weakref
    _weakrefset _winapi _wmi _zoneinfo _zstd abc annotationlib antigravity argparse
    array ast asyncio atexit base64 bdb binascii bisect builtins bz2 cProfile calendar
    cmath cmd code codecs codeop collections colorsys compileall compression concurrent
    configparser contextlib contextvars copy copyreg csv ctypes curses dataclasses
    datetime dbm decimal difflib dis doctest email encodings ensurepip enum errno
    faulthandler fcntl filecmp fileinput fnmatch fractions ftplib functools gc genericpath
    getopt getpass gettext glob graphlib grp gzip hashlib heapq hmac html http idlelib
    imaplib importlib inspect io ipaddress itertools json keyword linecache locale logging
    lzma mailbox marshal math mimetypes mmap modulefinder msvcrt multiprocessing netrc nt
    ntpath nturl2path numbers opcode operator optparse os pathlib pdb pickle pickletools
    pkgutil platform plistlib poplib posix posixpath pprint profile pstats pty pwd
    py_compile pyclbr pydoc pydoc_data pyexpat queue quopri random re readline reprlib
    resource rlcompleter runpy sched secrets select selectors shelve shlex shutil signal
    site smtplib socket socketserver sqlite3 sre_compile sre_constants sre_parse ssl stat
    statistics string stringprep struct subprocess symtable sys sysconfig syslog tabnanny
    tarfile tempfile termios textwrap this threading time timeit tkinter token tokenize
    tomllib trace traceback tracemalloc tty turtle turtledemo types typing unicodedata
    unittest urllib uuid venv warnings wave weakref webbrowser winreg winsound wsgiref xml
    xmlrpc zipapp zipfile zipimport zlib zoneinfo
    """.split()
)
_DEPENDENCY_IMPORT_ALIASES: dict[str, frozenset[str]] = {
    "beautifulsoup4": frozenset({"bs4"}),
    "pillow": frozenset({"PIL"}),
    "pydantic-core": frozenset({"pydantic_core"}),
    "pyyaml": frozenset({"yaml"}),
    "regex": frozenset({"regex"}),
}


@lru_cache(maxsize=1)
def _installed_distribution_import_roots() -> dict[str, frozenset[str]]:
    roots_by_project: dict[str, set[str]] = {}
    for import_root, projects in metadata.packages_distributions().items():
        for project in projects:
            canonical = re.sub(r"[-_.]+", "-", project).lower()
            roots_by_project.setdefault(canonical, set()).add(import_root)
    return {
        project: frozenset(import_roots)
        for project, import_roots in roots_by_project.items()
    }


def _dependency_import_roots(declared_deps: tuple[str, ...]) -> frozenset[str] | None:
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    roots: set[str] = set()
    for dependency in declared_deps:
        project = Requirement(dependency).name
        canonical = canonicalize_name(project)
        project_roots = set(_DEPENDENCY_IMPORT_ALIASES.get(canonical, ()))
        project_roots.update(_installed_distribution_import_roots().get(canonical, ()))
        if not project_roots:
            return None
        roots.update(project_roots)
    return frozenset(roots)


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


def _validate_portable_source(
    name: str,
    source: str,
    *,
    allow_dependencies: bool = False,
    validate_dependency_imports: bool = True,
    validate_source_size: bool = True,
) -> None:
    source_bytes = source.encode("utf-8")
    if validate_source_size and len(source_bytes) > MAX_BUNDLE_PURE_SOURCE_BYTES:
        raise ValueError(
            f"pure {name!r} source is too large for the wasm tier "
            f"({len(source_bytes)} bytes; limit {MAX_BUNDLE_PURE_SOURCE_BYTES})"
        )

    declared_deps, _ = parse_pep723(source)
    if declared_deps and not allow_dependencies:
        raise ValueError(
            f"pure {name!r} declares third-party dependencies; the wasm alpha "
            "supports dependency-free pures only"
        )

    tree = ast.parse(source)
    third_party: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.partition(".")[0]
                if root not in _WASM_GUEST_STDLIB_MODULES:
                    third_party.add(root)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                raise ValueError(
                    f"pure {name!r} uses a relative import; bundle pure source "
                    "executes as a standalone module"
                )
            root = (node.module or "").partition(".")[0]
            if root and root not in _WASM_GUEST_STDLIB_MODULES:
                third_party.add(root)
    if third_party and (not allow_dependencies or not declared_deps):
        raise ValueError(
            f"pure {name!r} imports unsupported module(s) "
            f"{', '.join(sorted(third_party))}; third-party imports require declared "
            "dependencies and an enabled dependency tier"
        )
    if third_party and validate_dependency_imports:
        allowed_imports = _dependency_import_roots(declared_deps)
        mismatched = third_party - allowed_imports if allowed_imports is not None else set()
        if mismatched:
            raise ValueError(
                f"pure {name!r} imports module(s) {', '.join(sorted(mismatched))} "
                "that are not supplied by its declared dependencies"
            )


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
class RendererDependency:
    """One ordered dependency captured into a renderer's source hash."""

    kind: str
    ref: str
    rel: str
    content: str
    exists: bool


@dataclass(frozen=True)
class RendererDeclaration:
    """Portable inputs for rebuilding one data-backed renderer."""

    package: str
    role: str
    source: str
    base_dir: Optional[str]
    templates: Mapping[str, str]
    files: Mapping[str, str]
    hash_source: str
    dependencies: tuple[RendererDependency, ...]


@dataclass(frozen=True)
class ToolSchemaExpectation:
    """The prompt-side tool contract a dotctx package was written against.

    Recorded at load (``tools.pyi``); compared by canonical hash against the
    served schema when freeze resolves the tool (``TOOL_SCHEMA_DRIFT``).
    """

    key: str                        # toolref key: native name or "server/tool"
    input_schema: dict[str, Any]    # expected JSON Schema for the tool input
    ctx_path: str                   # the .ctx package that recorded it
    description: str = ""           # provider-visible tools.pyi docstring summary


def scoped_tool_expectation_key(scope: str, key: str) -> str:
    """Internal key for a package-local bare tool name.

    Bare provider names deliberately belong to a dotctx package, not to the
    process.  The NUL separator cannot occur in either authored identifier and
    avoids accidentally treating a wire ToolRef as a scoped entry.
    """
    return f"{scope}\0{key}"


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


def _has_module_top_pep723_block(module_source: str) -> bool:
    """Return ``True`` when the module header looks like a PEP 723 block.

    We only inspect the preamble before the first top-level decorator or ``def``.
    That catches a module-top block, which ``inspect.getsource(fn)`` would miss,
    while still allowing the supported placement between ``@pure(...)`` and ``def``.
    """
    lines = module_source.splitlines()
    first_defn = len(lines)
    for idx, line in enumerate(lines):
        if line.startswith(("@", "def ", "async def ")):
            first_defn = idx
            break
    preamble = "\n".join(lines[:first_defn])
    try:
        deps, requires_python = parse_pep723(preamble)
    except ValueError:
        return True
    return bool(deps) or requires_python is not None


class Registry:
    """An explicit registry for named reasoners and deterministic pure functions."""

    def __init__(self) -> None:
        self.reasoners: dict[str, Reasoner] = {}
        self.pures: dict[str, PureEntry] = {}
        self.renderers: dict[str, RendererEntry] = {}
        self.renderer_declarations: dict[str, RendererDeclaration] = {}
        # Content-addressed agent skills (skill/<name>@v<hash12>). Keys carry
        # their own content hash, so sharing them process-wide is safe.
        self.skills: dict[str, Skill] = {}
        self.tool_expectations: dict[str, ToolSchemaExpectation] = {}
        # Compatibility aliases installed by a scoped dotctx package are kept
        # queryable, but must not constrain unrelated top-level native calls
        # that happen to reuse the same bare tool name.
        self.scoped_tool_fallbacks: set[str] = set()
        # Release-hydrated AgentWorkflow specs keyed by controller name.
        self.agent_specs: dict[str, dict[str, Any]] = {}

    def register_reasoner(self, reasoner: Reasoner) -> Reasoner:
        if reasoner.name in self.reasoners and self.reasoners[reasoner.name] != reasoner:
            raise ValueError(f"reasoner {reasoner.name!r} already registered with a different config")
        self.reasoners[reasoner.name] = reasoner
        return reasoner

    def get_reasoner(self, name: str) -> Reasoner:
        try:
            return self.reasoners[name]
        except KeyError as e:
            raise KeyError(f"unknown reasoner {name!r}; load its dotctx with load_dotctx()") from e

    def list_reasoners(self) -> list[str]:
        return sorted(self.reasoners)

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
            if not deps:
                module = inspect.getmodule(fn)
                module_source = None
                if module is not None:
                    try:
                        module_source = inspect.getsource(module)
                    except (OSError, TypeError):
                        module_source = None
                if module_source is not None and _has_module_top_pep723_block(module_source):
                    raise ValueError(
                        f"pure {name!r}: a PEP 723 `# /// script` block is placed at module "
                        "top, where register_pure cannot see it. Move it between the "
                        "`@pure(...)` decorator and `def`."
                    )
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

    def register_pure_with_source(
        self,
        name: str,
        fn: PureFn,
        source: str,
    ) -> PureEntry:
        source_hash = _text_hash(source)
        existing = self.pures.get(name)
        if existing is not None:
            if existing.source_hash == source_hash:
                return existing
            raise ValueError(
                f"pure name {name!r} registered with different source: "
                f"{existing.source_hash} != {source_hash}"
            )
        deps, requires_python = parse_pep723(source)
        entry = PureEntry(
            name=name,
            fn=fn,
            source_hash=source_hash,
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
        validate_dependency_imports: bool = True,
        validate_source_size: bool = True,
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

        _validate_portable_source(
            name,
            source,
            allow_dependencies=True,
            validate_dependency_imports=validate_dependency_imports,
            validate_source_size=validate_source_size,
        )
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

    def executor_of(self, name: str) -> str:
        try:
            return self.pures[name].executor
        except KeyError as e:
            raise KeyError(
                f"unknown pure {name!r}; register it with @pure({name!r}) on a worker"
            ) from e

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

    def register_skill(self, skill: Skill) -> str:
        """Register a skill under its content key and return that key.

        ``Skill`` equality ignores ``source``, so byte-identical sidecars in
        different packages register once. A genuine mismatch under one key is
        impossible (the key hashes every compared field) and is treated as a
        corrupt-input error rather than silently overwritten.
        """
        key = skill_key(skill)
        existing = self.skills.get(key)
        if existing is not None and existing != skill:
            raise ValueError(
                f"skill key {key!r} already registered with different content"
            )
        self.skills[key] = skill
        return key

    def get_skill(self, key: str) -> Skill:
        try:
            return self.skills[key]
        except KeyError as e:
            raise KeyError(
                f"unknown skill {key!r}; load its dotctx package or call "
                "register_skill()"
            ) from e

    def renderer_source_hash_of(self, name: str) -> str:
        return self.renderers[name].source_hash

    def register_tool_expectation(
        self,
        exp: ToolSchemaExpectation,
        *,
        scope: Optional[str] = None,
    ) -> ToolSchemaExpectation:
        storage_key = (
            scoped_tool_expectation_key(scope, exp.key)
            if scope is not None
            else exp.key
        )
        existing = self.tool_expectations.get(storage_key)
        if existing is not None and existing.input_schema != exp.input_schema:
            raise ValueError(
                f"conflicting expected schemas for tool {exp.key!r}: "
                f"{existing.ctx_path!r} vs {exp.ctx_path!r}"
            )
        self.tool_expectations[storage_key] = exp
        # Retain the historical unscoped lookup for callers loading one package.
        # A second package may reuse the same model-visible alias with a different
        # schema; its scoped entry remains authoritative at freeze.
        if scope is None:
            self.scoped_tool_fallbacks.discard(exp.key)
        elif exp.key not in self.tool_expectations:
            self.tool_expectations[exp.key] = exp
            self.scoped_tool_fallbacks.add(exp.key)
        return exp

    def get_tool_expectation(
        self,
        key: str,
        *,
        scope: Optional[str] = None,
    ) -> Optional[ToolSchemaExpectation]:
        if scope is not None:
            scoped = self.tool_expectations.get(scoped_tool_expectation_key(scope, key))
            if scoped is not None:
                return scoped
        return self.tool_expectations.get(key)

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
