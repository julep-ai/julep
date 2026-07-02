"""The rich dotctx layout (design: docs/design/dotctx-rich-format.md).

A rich ``.ctx`` package grows the minimal layout with Jinja2 templates
(``prompt.j2`` — optionally split into system/user sections by mem-mcp's
``<<< role:... >>>`` markers — or a ``messages/`` bundle of one system + one
user message),
``schema.pyi`` (an ``Output`` stub compiled to JSON Schema ->
``Reasoner.reply_schema``) and ``tools.pyi`` (tool stubs -> granted toolref keys +
expected input schemas, verified at freeze as ``TOOL_SCHEMA_DRIFT``).

Templates are never stored on the :class:`~composable_agents.dotctx.Reasoner` and
never enter the deploy artifact. Loading compiles each template and registers
one renderer per template — ``dotctx/<package>/<role>@v<content-hash-prefix>``
— hashed by template content like any registered pure, so §6.4 drift detection
covers prompt edits. The Reasoner carries only the renderer *names*
(``system_render`` / ``user_render``); ``Reasoner.system`` stays ``""``.

``eval.py`` / ``eval.yaml`` are a consumer-side contract and are never loaded
here — :func:`composable_agents.dotctx_evals.load_ctx_evals` is the explicit
entry point (loading a prompt must never execute eval code).
Requires the ``composable-agents[dotctx]`` extra; importing this module without
jinja2 is a hard error — a package that has a template and a loader that cannot
render it must not fall back to a plain string (G-8).
"""

from __future__ import annotations

import ast
import hashlib
import html
import importlib
import json
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, cast

try:
    import jinja2
    from jinja2 import meta as jinja2_meta
except ImportError as e:  # pragma: no cover - exercised via sys.modules patching
    raise ImportError(
        "jinja2 is required for the rich dotctx layout (prompt.j2 / messages/); "
        "install composable-agents[dotctx]"
    ) from e

from .capabilities import ToolGrant
from .dotctx import (
    Reasoner,
    _as_float,
    _as_int,
    _model_and_effort,
    _require_tool_call_setting,
    _response_format_setting,
    _setting,
    _sub_from,
)
from .kinds import ContextScope
from .registry import DEFAULT_REGISTRY, Registry, ToolSchemaExpectation

# Settings keys the rich layout accepts. The prompt lives in template files and
# the reply schema in schema.pyi, so the minimal layout's system/schema keys are
# deliberately absent. Unknown keys are a load-time error, not a warning.
_ALLOWED_SETTINGS = frozenset(
    {
        "name",
        "model",
        "temperature",
        "max_rounds",
        "maxRounds",
        "max_tokens",
        "maxTokens",
        "reasoning_effort",
        "reasoningEffort",
        "output_retries",
        "outputRetries",
        "require_tool_call",
        "requireToolCall",
        "response_format",
        "responseFormat",
        "agent",
        "sub",
        "context",
        "tools",
    }
)

_HASH_PREFIX_LEN = 12


@dataclass(frozen=True)
class ToolStub:
    """One ``tools.pyi`` function stub: the prompt-side tool contract."""

    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class RichDotctx:
    """A loaded rich package: the Reasoner plus what the caller merges/verifies.

    ``tool_grants`` is the manifest fragment for the deployment's
    CapabilityManifest — the package declares what it needs; the deployment
    decides what is granted. ``expected_tool_schemas`` (toolref key -> JSON
    Schema) is also recorded in the registry for the freeze-time
    ``TOOL_SCHEMA_DRIFT`` check.
    """

    reasoner: Reasoner
    path: str
    package: str
    renderer_names: Mapping[str, str]  # role -> registered renderer name
    tool_grants: tuple[ToolGrant, ...]
    expected_tool_schemas: Mapping[str, dict[str, Any]]


# --------------------------------------------------------------------------- #
# mem-mcp's custom Jinja filters (dotctx filters.py, ported 1:1 for the pure
# ones — briefs/draft.ctx alone uses `to_json` 20+ times, and jinja resolves
# filter names at compile time, so loading needs them registered). The
# file/token filters (import_yaml, import_text, count_tokens, truncate_tokens)
# need mem-mcp's base_dir / tiktoken wiring; they register as render-time
# teaching errors so those templates still load (G-8: loud, never silent).
# --------------------------------------------------------------------------- #
def _filter_as_xml(value: Any, tag: str = "data") -> str:
    content = str(value) if value is not None else ""
    return f"<{tag}>{html.escape(content, quote=False)}</{tag}>"


def _filter_as_codeblock(value: str, lang: str = "") -> str:
    return f"```{lang}\n{value}\n```"


def _filter_numbered_list(items: Sequence[Any], start: int = 1) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start))


def _filter_bulleted_list(items: Sequence[Any], bullet: str = "-") -> str:
    return "\n".join(f"{bullet} {item}" for item in items)


def _filter_to_json(value: Any, indent: Optional[int] = None) -> str:
    return json.dumps(value, indent=indent, ensure_ascii=False)


def _resolve_file_filter_path(path: str, base_dir: Optional[str]) -> Path:
    file_path = Path(path)
    if not file_path.is_absolute() and base_dir is not None:
        file_path = Path(base_dir) / file_path
    return file_path


def _snapshot_key(path: str, base_dir: Optional[str]) -> str:
    return os.path.normpath(str(_resolve_file_filter_path(path, base_dir)))


def _snapshot_content(
    path: str, base_dir: Optional[str], files: Mapping[str, str]
) -> str:
    """The captured bytes for a file-import filter arg — never a live read.

    Rendering from anything but the load-time snapshot would let an on-disk
    edit change the prompt behind an unchanged renderer hash. Only literal
    ``'<path>' | import_yaml/import_text`` args are captured, so a variable
    path (or a file missing at load) is a loud error here.
    """
    key = _snapshot_key(path, base_dir)
    if key not in files:
        raise ValueError(
            f"import path {path!r} was not captured when the dotctx was "
            "loaded; import_yaml/import_text support only literal string "
            "paths to files that exist at load time"
        )
    return files[key]


def _filter_import_yaml(
    path: str, base_dir: Optional[str], files: Mapping[str, str]
) -> Any:
    import yaml

    return yaml.safe_load(_snapshot_content(path, base_dir, files))


def _filter_import_text(
    path: str, base_dir: Optional[str], files: Mapping[str, str]
) -> str:
    return _snapshot_content(path, base_dir, files)


def _encoding_for_model(model: str) -> Any:
    try:
        tiktoken = importlib.import_module("tiktoken")
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise ValueError(
            "the 'count_tokens' and 'truncate_tokens' dotctx filters require tiktoken"
        ) from exc
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def _filter_count_tokens(text: str, model: str = "gpt-4") -> int:
    return len(_encoding_for_model(model).encode(text))


def _filter_truncate_tokens(
    text: str,
    max_tokens: int,
    model: str = "gpt-4",
    suffix: str = "...",
) -> str:
    encoding = _encoding_for_model(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    suffix_tokens = encoding.encode(suffix)
    truncate_at = max_tokens - len(suffix_tokens)
    if truncate_at <= 0:
        return suffix
    return cast(str, encoding.decode(tokens[:truncate_at])) + suffix


def _memmcp_filters(
    base_dir: Optional[str], files: Mapping[str, str]
) -> dict[str, Callable[..., Any]]:
    return {
        "as_xml": _filter_as_xml,
        "as_codeblock": _filter_as_codeblock,
        "numbered_list": _filter_numbered_list,
        "bulleted_list": _filter_bulleted_list,
        "count_tokens": _filter_count_tokens,
        "truncate_tokens": _filter_truncate_tokens,
        "dedent": textwrap.dedent,
        "import_yaml": lambda p: _filter_import_yaml(p, base_dir, files),
        "import_text": lambda p: _filter_import_text(p, base_dir, files),
        "to_json": _filter_to_json,
        "from_json": json.loads,
    }


# --------------------------------------------------------------------------- #
# Templates -> registered renderers.
# --------------------------------------------------------------------------- #
def _template_renderer(
    package: str,
    role: str,
    source: str,
    base_dir: Optional[str],
    templates: Mapping[str, str],
    files: Mapping[str, str],
) -> Callable[[Mapping[str, Any]], str]:
    # Includes and file imports are served from the load-time snapshot that
    # the renderer hash covers — never the live filesystem — so a dep edit
    # after load cannot change the prompt behind an unchanged hash.
    env = jinja2.Environment(
        loader=jinja2.DictLoader(dict(templates)),
        extensions=["jinja2.ext.loopcontrols"],
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(_memmcp_filters(base_dir, files))
    template = env.from_string(source)

    def render(ctx: Mapping[str, Any]) -> str:
        try:
            return template.render(dict(ctx))
        except jinja2.UndefinedError as exc:
            raise ValueError(
                f"dotctx package {package!r} {role} template: {exc}"
            ) from exc

    return render


_IMPORT_FILE_FILTER_RE = re.compile(
    r"""(?P<quote>['"])(?P<path>[^'"]+)(?P=quote)\s*\|\s*(?P<filter>import_yaml|import_text)\b"""
)


def _rel_dependency(path: Path, base_dir: str) -> str:
    try:
        return os.path.relpath(path, base_dir)
    except ValueError:
        return str(path)


def _dependency_path(base_dir: str, ref: str) -> Path:
    path = Path(ref)
    if path.is_absolute():
        return path
    return Path(base_dir) / path


def _read_dependency(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"<missing: {exc}>"


@dataclass(frozen=True)
class _Dependency:
    """One captured include/import: hash label + render-time snapshot key."""

    kind: str        # "template" | "import_yaml" | "import_text"
    ref: str         # as written in the template: loader name / filter arg
    rel: str         # base_dir-relative label used in the hashed bundle
    content: str     # captured bytes ("<missing: ...>" sentinel when absent)
    exists: bool


def _template_dependencies(
    source: str,
    base_dir: Optional[str],
    seen: Optional[set[tuple[str, str]]] = None,
) -> list[_Dependency]:
    if base_dir is None:
        return []
    seen = seen if seen is not None else set()  # of (kind-scope, resolved path)
    deps: list[_Dependency] = []

    parsed = jinja2.Environment(extensions=["jinja2.ext.loopcontrols"]).parse(source)
    for ref in jinja2_meta.find_referenced_templates(parsed):
        if ref is None:
            # A computed include target can't be hashed or snapshotted; a live
            # read at render time would bypass drift detection entirely.
            raise ValueError(
                "dotctx template uses a dynamic include/import target; "
                "include/import/extends must name a literal template path so "
                "it can be captured into the renderer hash"
            )
        path = _dependency_path(base_dir, ref)
        # Dedup is kind-qualified: the same file may be both included as a
        # template and read via an import filter, and each use needs its own
        # snapshot entry.
        key = ("template", str(path.resolve()) if path.exists() else str(path))
        if key in seen:
            continue
        seen.add(key)
        content = _read_dependency(path)
        deps.append(_Dependency(
            "template", ref, _rel_dependency(path, base_dir), content, path.exists(),
        ))
        deps.extend(_template_dependencies(content, base_dir, seen))

    for match in _IMPORT_FILE_FILTER_RE.finditer(source):
        ref = match.group("path")
        path = _dependency_path(base_dir, ref)
        key = ("import", str(path.resolve()) if path.exists() else str(path))
        if key in seen:
            continue
        seen.add(key)
        deps.append(_Dependency(
            match.group("filter"), ref, _rel_dependency(path, base_dir),
            _read_dependency(path), path.exists(),
        ))

    return deps


def _source_with_dependencies(source: str, deps: Sequence[_Dependency]) -> str:
    if not deps:
        return source
    chunks = [source, "\n\n# dotctx dependency bundle\n"]
    for dep in deps:
        chunks.append(f"\n# {dep.kind}: {dep.rel}\n{dep.content}")
    return "".join(chunks)


def _register_template(
    registry: Registry,
    package: str,
    role: str,
    source: str,
    *,
    base_dir: Optional[str],
) -> str:
    deps = _template_dependencies(source, base_dir)
    source_for_hash = _source_with_dependencies(source, deps)
    # The renderer serves includes/imports from this same captured set, so the
    # hash and the rendered prompt can never disagree. Missing files stay out:
    # a missing include keeps raising TemplateNotFound at render.
    templates = {
        d.ref: d.content for d in deps if d.kind == "template" and d.exists
    }
    files = {
        _snapshot_key(d.ref, base_dir): d.content
        for d in deps if d.kind in ("import_yaml", "import_text") and d.exists
    }
    digest = hashlib.sha256(source_for_hash.encode("utf-8")).hexdigest()
    name = f"dotctx/{package}/{role}@v{digest[:_HASH_PREFIX_LEN]}"
    if name not in registry.renderers:  # same name => same content; reload is a no-op
        registry.register_renderer(
            name,
            _template_renderer(package, role, source, base_dir, templates, files),
            source=source_for_hash,
        )
    return name


# mem-mcp's single-file multi-message format: <<< role:name >>> markers split a
# template into per-role sections (loader.py ROLE_MARKER_PATTERN). Spacing is
# flexible — <<<role:system>>> matches too — but bare <<< / >>> heredoc
# delimiters in prompt bodies do not (no ``role:``).
_ROLE_MARKER_RE = re.compile(r"<<<\s*role:(\w+)\s*>>>")
_JINJA_COMMENT_RE = re.compile(r"\{#.*?#\}", re.DOTALL)


def _split_role_markers(source: str, origin: str) -> Optional[tuple[str, Optional[str]]]:
    """Split ``<<< role:... >>>`` markers into (system source, user source).

    Returns ``None`` when the source has no markers (whole file stays the
    system template). v1 accepts exactly the shapes a ``messages/`` bundle
    accepts: one system section optionally followed by one user section;
    anything else is rejected loudly with the file name and offending role.
    Content before the first marker must be whitespace, Jinja comments, or
    bare ``#`` comment lines only. Jinja comments are prepended to the system
    section source so headers like ``{# AI-ANCHOR #}`` stay in the hashed
    template while rendering to nothing; ``#`` header lines (mem-mcp's
    AI-ANCHOR convention in a few real ``.j2`` files, e.g.
    ``clustering/cluster_label.ctx``) are dropped — mem-mcp discards all
    pre-marker content, and prepending them would render visible text.
    """
    parts = _ROLE_MARKER_RE.split(source)
    if len(parts) == 1:
        return None

    pre = parts[0]
    # Mask Jinja comments (newlines kept, other chars removed) so the per-line
    # checks below only see text living outside {# ... #}.
    masked = _JINJA_COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", "", m.group(0)), pre)
    kept: list[str] = []
    for raw_line, visible in zip(pre.splitlines(), masked.splitlines(), strict=True):
        text = visible.strip()
        if not text:
            kept.append(raw_line)  # whitespace / Jinja-comment content
        elif not text.startswith("#"):
            raise ValueError(
                f"dotctx template {origin!r} has content before the first "
                "<<< role:... >>> marker; only whitespace, Jinja comments "
                "({# ... #}), or # comment lines may precede it"
            )
    pre = "\n".join(kept)

    # parts: [pre, role1, content1, role2, content2, ...]; contents stripped
    # like mem-mcp's _parse_role_markers.
    sections = list(zip(
        (role.strip().lower() for role in parts[1::2]),
        (c.strip() for c in parts[2::2]),
        strict=True,
    ))
    expected = ("system", "user")
    for (role, _), want in zip(sections, expected, strict=False):
        if role != want:
            raise ValueError(
                f"dotctx template {origin!r} has role marker {role!r} where "
                f"{want!r} was expected; v1 accepts one system section "
                "optionally followed by one user section"
            )
    if len(sections) > 2:
        raise ValueError(
            f"dotctx template {origin!r} has extra role marker "
            f"{sections[2][0]!r}; v1 accepts one system section optionally "
            "followed by one user section"
        )

    header = pre.strip()
    system = f"{header}{sections[0][1]}" if header else sections[0][1]
    user = sections[1][1] if len(sections) == 2 else None
    return system, user


def _read_messages(messages_dir: str) -> tuple[Optional[str], Optional[str]]:
    """Parse a ``messages/`` bundle into (system body, user body).

    v1 accepts exactly one system message optionally followed by one user
    message; anything else is rejected loudly with the file name.
    """
    import yaml

    files = sorted(
        fn for fn in os.listdir(messages_dir) if fn.endswith((".yml", ".yaml"))
    )
    roles: list[tuple[str, str, str]] = []  # (role, body, filename)
    for fn in files:
        full = os.path.join(messages_dir, fn)
        with open(full, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"dotctx message {fn!r} must be a YAML mapping with role + content")
        extra = sorted(set(data) - {"role", "content"})
        if extra:
            raise ValueError(f"dotctx message {fn!r} has unknown keys: {', '.join(extra)}")
        role = data.get("role")
        content = data.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            raise ValueError(f"dotctx message {fn!r} needs string 'role' and 'content'")
        roles.append((role, content, fn))

    if not roles:
        return None, None
    expected = ("system", "user")
    if len(roles) > 2:
        raise ValueError(
            f"dotctx message bundle supports one system + one user message; "
            f"extra message file {roles[2][2]!r}"
        )
    for (role, _, fn), want in zip(roles, expected, strict=False):
        if role != want:
            raise ValueError(
                f"dotctx message {fn!r} has role {role!r}; v1 bundles are one "
                "system message optionally followed by one user message"
            )
    system = roles[0][1]
    user = roles[1][1] if len(roles) == 2 else None
    return system, user


def _read_templates(path: str) -> tuple[Optional[str], Optional[str]]:
    prompt_path = os.path.join(path, "prompt.j2")
    messages_dir = os.path.join(path, "messages")
    has_prompt = os.path.exists(prompt_path)
    has_messages = os.path.isdir(messages_dir)
    if has_prompt and has_messages:
        raise ValueError(f"dotctx package {path!r} has both prompt.j2 and messages/; pick one")
    if has_prompt:
        with open(prompt_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        split = _split_role_markers(source, prompt_path)
        if split is not None:
            return split
        return source, None
    if has_messages:
        return _read_messages(messages_dir)
    return None, None


# --------------------------------------------------------------------------- #
# .pyi compilation (stdlib ast only — JSON Schema in, JSON out; no pydantic).
# --------------------------------------------------------------------------- #
_NAME_SCHEMAS: dict[str, dict[str, Any]] = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "Any": {},
    "None": {"type": "null"},
    # Bare containers: unconstrained items/properties.
    "list": {"type": "array", "items": {}},
    "dict": {"type": "object"},
    "set": {"type": "array", "items": {}, "uniqueItems": True},
    "tuple": {"type": "array", "items": {}},
}

_GENERIC_ALIASES = {"List": "list", "Dict": "dict", "Set": "set", "Tuple": "tuple"}

ClassResolver = Callable[[str], dict[str, Any]]


def _subscript_name(node: ast.Subscript) -> str:
    if isinstance(node.value, ast.Name):
        name = node.value.id
    elif isinstance(node.value, ast.Attribute):
        name = node.value.attr
    else:
        raise ValueError(f"unsupported subscript base: {ast.dump(node.value)}")
    return _GENERIC_ALIASES.get(name, name)


def _nullable(schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type") == "null":
        return schema
    return {"anyOf": [schema, {"type": "null"}]}


def _literal_schema(node: ast.expr) -> dict[str, Any]:
    elts = node.elts if isinstance(node, ast.Tuple) else [node]
    values = [e.value for e in elts if isinstance(e, ast.Constant)]
    if not values:
        raise ValueError("Literal[...] needs constant values")
    if all(isinstance(v, str) for v in values):
        return {"type": "string", "enum": values}
    if all(isinstance(v, bool) for v in values):
        return {"type": "boolean", "enum": values}
    if all(isinstance(v, int) for v in values):
        return {"type": "integer", "enum": values}
    return {"enum": values}


def _annotation_schema(node: ast.expr, resolver: ClassResolver) -> dict[str, Any]:
    """Map a stub type annotation to JSON Schema (the pragmatic subset)."""
    if isinstance(node, ast.Name):
        if node.id in _NAME_SCHEMAS:
            return dict(_NAME_SCHEMAS[node.id])
        return resolver(node.id)
    if isinstance(node, ast.Attribute):  # typing.Optional etc.
        return _annotation_schema(ast.Name(id=node.attr, ctx=ast.Load()), resolver)
    if isinstance(node, ast.Constant) and node.value is None:
        return {"type": "null"}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = node.left, node.right
        if isinstance(right, ast.Constant) and right.value is None:
            return _nullable(_annotation_schema(left, resolver))
        if isinstance(left, ast.Constant) and left.value is None:
            return _nullable(_annotation_schema(right, resolver))
        return {
            "anyOf": [
                _annotation_schema(left, resolver),
                _annotation_schema(right, resolver),
            ]
        }
    if isinstance(node, ast.Subscript):
        base = _subscript_name(node)
        if base == "list":
            return {"type": "array", "items": _annotation_schema(node.slice, resolver)}
        if base == "set":
            return {
                "type": "array",
                "items": _annotation_schema(node.slice, resolver),
                "uniqueItems": True,
            }
        if base == "tuple":
            if isinstance(node.slice, ast.Tuple):
                elts = node.slice.elts
                if (
                    len(elts) == 2
                    and isinstance(elts[1], ast.Constant)
                    and elts[1].value is ...
                ):
                    return {"type": "array", "items": _annotation_schema(elts[0], resolver)}
                return {
                    "type": "array",
                    "prefixItems": [_annotation_schema(e, resolver) for e in elts],
                    "items": False,
                }
            return {"type": "array", "items": _annotation_schema(node.slice, resolver)}
        if base == "dict":
            if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                return {
                    "type": "object",
                    "additionalProperties": _annotation_schema(node.slice.elts[1], resolver),
                }
            return {"type": "object"}
        if base == "Literal":
            return _literal_schema(node.slice)
        if base == "Optional":
            return _nullable(_annotation_schema(node.slice, resolver))
        if base in ("Required", "NotRequired"):
            return _annotation_schema(node.slice, resolver)
        raise ValueError(f"unsupported generic type: {base}[...]")
    raise ValueError(f"unsupported annotation: {ast.dump(node)}")


def _is_optional_annotation(node: ast.expr) -> bool:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        for side in (node.left, node.right):
            if isinstance(side, ast.Constant) and side.value is None:
                return True
        return _is_optional_annotation(node.left) or _is_optional_annotation(node.right)
    if isinstance(node, ast.Subscript):
        try:
            return _subscript_name(node) == "Optional"
        except ValueError:
            return False
    return False


def _constant_value(node: ast.expr) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_constant_value(e) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return [_constant_value(e) for e in node.elts]
    if isinstance(node, ast.Dict):
        return {
            (_constant_value(k) if k is not None else None): _constant_value(v)
            for k, v in zip(node.keys, node.values, strict=True)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        operand = _constant_value(node.operand)
        if isinstance(operand, (int, float)):
            return -operand
    return None


def _is_typeddict_class(node: ast.ClassDef, class_defs: dict[str, ast.ClassDef]) -> bool:
    def is_td_base(base: ast.expr) -> bool:
        if isinstance(base, ast.Name):
            if base.id == "TypedDict":
                return True
            inner = class_defs.get(base.id)
            return inner is not None and _is_typeddict_class(inner, class_defs)
        return isinstance(base, ast.Attribute) and base.attr == "TypedDict"

    return any(is_td_base(b) for b in node.bases)


def _unwrap_required(node: ast.expr) -> tuple[ast.expr, Optional[bool]]:
    if isinstance(node, ast.Subscript):
        try:
            base = _subscript_name(node)
        except ValueError:
            return node, None
        if base == "Required":
            return node.slice, True
        if base == "NotRequired":
            return node.slice, False
    return node, None


def _class_schema(
    node: ast.ClassDef,
    class_defs: dict[str, ast.ClassDef],
    cache: dict[str, dict[str, Any]],
    in_progress: set[str],
) -> dict[str, Any]:
    def resolver(name: str) -> dict[str, Any]:
        return _resolve_class(name, class_defs, cache, in_progress)

    is_typeddict = _is_typeddict_class(node, class_defs)
    total = True
    for kw in node.keywords:
        if kw.arg == "total" and isinstance(kw.value, ast.Constant):
            total = bool(kw.value.value)

    properties: dict[str, Any] = {}
    required: set[str] = set()
    order: list[str] = []

    if is_typeddict:  # inline TypedDict bases
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in class_defs:
                base_schema = resolver(base.id)
                for key, value in base_schema.get("properties", {}).items():
                    properties[key] = value
                    order.append(key)
                required.update(base_schema.get("required", []))

    for item in node.body:
        if not (isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)):
            continue
        field = item.target.id
        annotation = item.annotation
        required_override: Optional[bool] = None
        if is_typeddict:
            annotation, required_override = _unwrap_required(annotation)
        try:
            schema = _annotation_schema(annotation, resolver)
        except ValueError as exc:
            raise ValueError(f"{node.name}.{field}: {exc}") from exc
        if item.value is not None:
            default = _constant_value(item.value)
            if default is not None:
                schema["default"] = default
        properties[field] = schema
        if field not in order:
            order.append(field)

        if is_typeddict:
            if required_override is not None:
                (required.add if required_override else required.discard)(field)
            elif total:
                required.add(field)
            else:
                required.discard(field)
        elif item.value is None and not _is_optional_annotation(annotation):
            required.add(field)

    out: dict[str, Any] = {"type": "object", "properties": properties}
    req = [f for f in order if f in required] if not is_typeddict else sorted(required)
    if req:
        out["required"] = req
    docstring = ast.get_docstring(node)
    if docstring:
        out["description"] = docstring
    return out


def _resolve_class(
    name: str,
    class_defs: dict[str, ast.ClassDef],
    cache: dict[str, dict[str, Any]],
    in_progress: set[str],
) -> dict[str, Any]:
    if name in cache:
        return cache[name]
    if name in in_progress:
        raise ValueError(f"recursive schema types are not supported: {name}")
    node = class_defs.get(name)
    if node is None:
        raise ValueError(f"unknown schema class: {name}")
    in_progress.add(name)
    schema = _class_schema(node, class_defs, cache, in_progress)
    in_progress.discard(name)
    cache[name] = schema
    return schema


def _module_classes(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {n.name: n for n in ast.iter_child_nodes(tree) if isinstance(n, ast.ClassDef)}


def parse_schema_pyi(source: str) -> Optional[dict[str, Any]]:
    """Compile the ``Output`` class of a ``schema.pyi`` to JSON Schema.

    ``Input`` (template variables) and any helper classes are not the reply
    contract; a schema.pyi without ``Output`` yields ``None``.
    """
    tree = ast.parse(source)
    class_defs = _module_classes(tree)
    if "Output" not in class_defs:
        return None
    return _resolve_class("Output", class_defs, {}, set())


# ----- tools.pyi ------------------------------------------------------------ #
_SECTION_HEADERS = ("Args:", "Returns:", "Raises:", "Examples:", "Yields:", "Attributes:")


def _docstring_description(docstring: str) -> str:
    first = re.split(r"\n\s*\n", docstring.strip())[0]
    lines: list[str] = []
    for line in first.split("\n"):
        stripped = line.strip()
        if stripped in _SECTION_HEADERS:
            break
        lines.append(stripped)
    return " ".join(lines).strip()


def _docstring_args(docstring: str) -> dict[str, str]:
    """Param descriptions from a Google-style ``Args:`` section."""
    args: dict[str, str] = {}
    in_args = False
    current: Optional[str] = None
    parts: list[str] = []

    def flush() -> None:
        nonlocal current, parts
        if current is not None:
            args[current] = " ".join(parts).strip()
        current, parts = None, []

    for line in docstring.split("\n"):
        stripped = line.strip()
        if stripped == "Args:":
            in_args = True
            continue
        if stripped in _SECTION_HEADERS:
            flush()
            in_args = False
            continue
        if not in_args:
            continue
        if not stripped:
            flush()
            continue
        match = re.match(r"^(\w+)\s*(?:\([^)]*\))?\s*:\s*(.*)$", stripped)
        if match:
            flush()
            current = match.group(1)
            parts = [match.group(2)] if match.group(2) else []
        elif current is not None:
            parts.append(stripped)
    flush()
    return args


def _function_stub(
    node: ast.FunctionDef | ast.AsyncFunctionDef, resolver: ClassResolver
) -> ToolStub:
    docstring = ast.get_docstring(node) or ""
    descriptions = _docstring_args(docstring)

    properties: dict[str, Any] = {}
    required: list[str] = []

    positional = node.args.args
    defaults: list[Optional[ast.expr]] = [None] * (
        len(positional) - len(node.args.defaults)
    ) + list(node.args.defaults)

    def add_param(arg: ast.arg, default: Optional[ast.expr]) -> None:
        if arg.arg in ("self", "cls"):
            return
        if arg.annotation is None:
            raise ValueError(f"{node.name}({arg.arg}): missing annotation")
        try:
            schema = _annotation_schema(arg.annotation, resolver)
        except ValueError as exc:
            raise ValueError(f"{node.name}({arg.arg}): {exc}") from exc
        if arg.arg in descriptions:
            schema["description"] = descriptions[arg.arg]
        if default is None:
            required.append(arg.arg)
        else:
            value = _constant_value(default)
            if value is not None:
                schema["default"] = value
        properties[arg.arg] = schema

    for arg, default in zip(positional, defaults, strict=True):
        add_param(arg, default)
    for arg, kw_default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
        add_param(arg, kw_default)

    input_schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        input_schema["required"] = required
    return ToolStub(
        name=node.name,
        description=_docstring_description(docstring),
        input_schema=input_schema,
    )


def parse_tools_pyi(source: str) -> tuple[Optional[str], list[ToolStub]]:
    """Compile ``tools.pyi`` stubs to (server name, tool stubs).

    A module-level ``__server__ = "<name>"`` assignment names the MCP server
    serving these tools (toolref keys become ``server/tool``); without it the
    stubs name native tools. The stubs do not create tools — they are the
    prompt-side contract assertion.
    """
    tree = ast.parse(source)
    class_defs = _module_classes(tree)
    cache: dict[str, dict[str, Any]] = {}

    def resolver(name: str) -> dict[str, Any]:
        return _resolve_class(name, class_defs, cache, set())

    server: Optional[str] = None
    stubs: list[ToolStub] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__server__":
                    if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                        raise ValueError("__server__ in tools.pyi must be a string literal")
                    server = node.value.value
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stubs.append(_function_stub(node, resolver))
    return server, stubs


# --------------------------------------------------------------------------- #
# The loader.
# --------------------------------------------------------------------------- #
def _parse_settings_text(
    text: str, *, env: Optional[Mapping[str, str]], origin: str
) -> dict[str, Any]:
    """Yglu-aware settings-text parsing shared by ``settings.yaml`` and
    single-file frontmatter (same gating, same explicit ``env`` binding)."""
    from .dotctx_yglu import has_yglu_tags, load_settings as load_yglu_settings

    if has_yglu_tags(text):
        loaded = load_yglu_settings(text, env=env, filepath=origin)
    else:
        import yaml

        loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"dotctx settings must be a YAML mapping: {origin!r}")
    return loaded


def _read_settings(path: str, *, env: Optional[Mapping[str, str]] = None) -> dict[str, Any]:
    for fn in ("settings.yaml", "settings.yml"):
        cand = os.path.join(path, fn)
        if os.path.exists(cand):
            with open(cand, "r", encoding="utf-8") as fh:
                text = fh.read()
            return _parse_settings_text(text, env=env, origin=cand)
    raise FileNotFoundError(f"no settings.yaml in dotctx dir: {path!r}")


def _validate_settings_keys(settings: Mapping[str, Any], origin: str) -> None:
    unknown = sorted(set(settings) - _ALLOWED_SETTINGS)
    if unknown:
        raise ValueError(
            f"unknown settings keys in {origin!r}: {', '.join(unknown)} "
            f"(allowed: {', '.join(sorted(_ALLOWED_SETTINGS))})"
        )


def _default_name(path: str) -> str:
    base = os.path.basename(os.path.normpath(path))
    return base[:-4] if base.endswith(".ctx") else base


def _template_base_dir(path: str) -> Optional[str]:
    """Default to mem-mcp's shared prompts root when a partials/ ancestor exists."""
    source = Path(path)
    start = source.parent if source.is_file() else source
    for candidate in (start, *start.parents):
        if (candidate / "partials").is_dir():
            return str(candidate)
    return str(start)


def _register_role_templates(
    registry: Registry,
    package: str,
    system_src: Optional[str],
    user_src: Optional[str],
    *,
    base_dir: Optional[str],
) -> dict[str, str]:
    renderer_names: dict[str, str] = {}
    if system_src is not None:
        renderer_names["system"] = _register_template(
            registry, package, "system", system_src, base_dir=base_dir
        )
    if user_src is not None:
        renderer_names["user"] = _register_template(
            registry, package, "user", user_src, base_dir=base_dir
        )
    return renderer_names


def _build_reasoner(
    package: str,
    settings: Mapping[str, Any],
    *,
    reply: Optional[dict[str, Any]],
    tools: tuple[str, ...],
    system_render: Optional[str],
    user_render: Optional[str],
) -> Reasoner:
    scope = ContextScope(settings["context"]) if settings.get("context") else ContextScope.LOCAL
    model, effort, output_retries = _model_and_effort(dict(settings))
    return Reasoner(
        name=package,
        model=model,
        system="",
        reply=reply,
        tools=tools,
        temperature=_as_float(settings.get("temperature"), key="temperature"),
        max_rounds=_as_int(_setting(settings, "max_rounds", "maxRounds"),
                           key="max_rounds"),
        is_agent=bool(settings.get("agent", False)),
        sub_contract=_sub_from(settings.get("sub")),
        context_scope=scope,
        system_render=system_render,
        user_render=user_render,
        max_tokens=_as_int(_setting(settings, "max_tokens", "maxTokens"),
                           key="max_tokens"),
        reasoning_effort=effort,
        output_retries=output_retries,
        require_tool_call=_require_tool_call_setting(settings),
        response_format=_response_format_setting(settings),
    )


# mem-mcp's single-file format: YAML frontmatter between --- delimiters, then
# the template body (loader.py FRONTMATTER_PATTERN). No match => no settings.
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def load_single_file_dotctx(
    path: str,
    *,
    registry: Registry = DEFAULT_REGISTRY,
    env: Optional[Mapping[str, str]] = None,
) -> RichDotctx:
    """Load a single-file ``.ctx``: YAML frontmatter + Jinja template body.

    The frontmatter goes through the same Yglu-aware settings path (and the
    same unknown-key validation) as ``settings.yaml``; the body through the
    same ``<<< role:... >>>`` splitting as ``prompt.j2``. A file without
    frontmatter is all template — settings are empty and CA's defaults apply.
    Nothing else can ride along in one file, so ``reply_schema`` stays ``None``
    and tools come from the frontmatter only.
    """
    if not path.endswith(".ctx"):
        raise ValueError(f"single-file dotctx must end in .ctx: {path!r}")
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    match = _FRONTMATTER_RE.match(content)
    if match:
        settings = _parse_settings_text(match.group(1), env=env, origin=path)
        body = match.group(2)
    else:
        settings, body = {}, content
    _validate_settings_keys(settings, path)

    raw_name = settings.get("name")
    package = raw_name if isinstance(raw_name, str) and raw_name else _default_name(path)

    split = _split_role_markers(body, path)
    system_src, user_src = split if split is not None else (body, None)
    base_dir = _template_base_dir(path)
    renderer_names = _register_role_templates(
        registry, package, system_src, user_src, base_dir=base_dir
    )

    settings_tools: Sequence[Any] = settings.get("tools") or ()
    reasoner = _build_reasoner(
        package,
        settings,
        reply=None,
        tools=tuple(dict.fromkeys(str(t) for t in settings_tools)),
        system_render=renderer_names.get("system"),
        user_render=renderer_names.get("user"),
    )
    reasoner = registry.register_reasoner(reasoner)

    return RichDotctx(
        reasoner=reasoner,
        path=path,
        package=package,
        renderer_names=renderer_names,
        tool_grants=(),
        expected_tool_schemas={},
    )


def load_rich_dotctx(
    path: str,
    *,
    registry: Registry = DEFAULT_REGISTRY,
    env: Optional[Mapping[str, str]] = None,
) -> RichDotctx:
    """Load a rich ``.ctx`` package: register renderers, reasoner, expectations.

    A ``path`` that is a *file* is the single-file frontmatter+body format and
    dispatches to :func:`load_single_file_dotctx`; directories keep the full
    layout below.
    """
    if os.path.isfile(path):
        return load_single_file_dotctx(path, registry=registry, env=env)

    settings = _read_settings(path, env=env)
    _validate_settings_keys(settings, path)

    raw_name = settings.get("name")
    package = raw_name if isinstance(raw_name, str) and raw_name else _default_name(path)

    system_src, user_src = _read_templates(path)
    base_dir = _template_base_dir(path)
    renderer_names = _register_role_templates(
        registry, package, system_src, user_src, base_dir=base_dir
    )

    reply_schema: Optional[dict[str, Any]] = None
    schema_path = os.path.join(path, "schema.pyi")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as fh:
            reply_schema = parse_schema_pyi(fh.read())

    tool_keys: list[str] = []
    expectations: dict[str, dict[str, Any]] = {}
    tools_path = os.path.join(path, "tools.pyi")
    if os.path.exists(tools_path):
        with open(tools_path, "r", encoding="utf-8") as fh:
            server, stubs = parse_tools_pyi(fh.read())
        for stub in stubs:
            key = f"{server}/{stub.name}" if server else stub.name
            tool_keys.append(key)
            expectations[key] = stub.input_schema
            registry.register_tool_expectation(
                ToolSchemaExpectation(key=key, input_schema=stub.input_schema, ctx_path=path)
            )

    settings_tools: Sequence[Any] = settings.get("tools") or ()
    tools = tuple(dict.fromkeys([*(str(t) for t in settings_tools), *tool_keys]))

    reasoner = _build_reasoner(
        package,
        settings,
        reply=reply_schema,
        tools=tools,
        system_render=renderer_names.get("system"),
        user_render=renderer_names.get("user"),
    )
    reasoner = registry.register_reasoner(reasoner)

    return RichDotctx(
        reasoner=reasoner,
        path=path,
        package=package,
        renderer_names=renderer_names,
        tool_grants=tuple(ToolGrant(name=key) for key in tool_keys),
        expected_tool_schemas=expectations,
    )


__all__ = [
    "RichDotctx",
    "ToolStub",
    "load_rich_dotctx",
    "load_single_file_dotctx",
    "parse_schema_pyi",
    "parse_tools_pyi",
]
