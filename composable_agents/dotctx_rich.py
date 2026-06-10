"""The rich dotctx layout (design: docs/design/dotctx-rich-format.md).

A rich ``.ctx`` package grows the minimal layout with Jinja2 templates
(``prompt.j2`` or a ``messages/`` bundle of one system + one user message),
``schema.pyi`` (an ``Output`` stub compiled to JSON Schema ->
``Brain.reply_schema``) and ``tools.pyi`` (tool stubs -> granted toolref keys +
expected input schemas, verified at freeze as ``TOOL_SCHEMA_DRIFT``).

Templates are never stored on the :class:`~composable_agents.dotctx.Brain` and
never enter the deploy artifact. Loading compiles each template and registers
one renderer per template — ``dotctx/<package>/<role>@v<content-hash-prefix>``
— hashed by template content like any registered pure, so §6.4 drift detection
covers prompt edits. The Brain carries only the renderer *names*
(``system_render`` / ``user_render``); ``Brain.system`` stays ``""``.

``eval.py`` / ``eval.yaml`` are a consumer-side contract and are ignored here.
Requires the ``composable-agents[dotctx]`` extra; importing this module without
jinja2 is a hard error — a package that has a template and a loader that cannot
render it must not fall back to a plain string (G-8).
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

try:
    import jinja2
except ImportError as e:  # pragma: no cover - exercised via sys.modules patching
    raise ImportError(
        "jinja2 is required for the rich dotctx layout (prompt.j2 / messages/); "
        "install composable-agents[dotctx]"
    ) from e

from .capabilities import ToolGrant
from .dotctx import Brain, _sub_from
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
    """A loaded rich package: the Brain plus what the caller merges/verifies.

    ``tool_grants`` is the manifest fragment for the deployment's
    CapabilityManifest — the package declares what it needs; the deployment
    decides what is granted. ``expected_tool_schemas`` (toolref key -> JSON
    Schema) is also recorded in the registry for the freeze-time
    ``TOOL_SCHEMA_DRIFT`` check.
    """

    brain: Brain
    path: str
    package: str
    renderer_names: Mapping[str, str]  # role -> registered renderer name
    tool_grants: tuple[ToolGrant, ...]
    expected_tool_schemas: Mapping[str, dict[str, Any]]


# --------------------------------------------------------------------------- #
# Templates -> registered renderers.
# --------------------------------------------------------------------------- #
def _template_renderer(
    package: str, role: str, source: str
) -> Callable[[Mapping[str, Any]], str]:
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    template = env.from_string(source)

    def render(ctx: Mapping[str, Any]) -> str:
        try:
            return template.render(dict(ctx))
        except jinja2.UndefinedError as exc:
            raise ValueError(
                f"dotctx package {package!r} {role} template: {exc}"
            ) from exc

    return render


def _register_template(registry: Registry, package: str, role: str, source: str) -> str:
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    name = f"dotctx/{package}/{role}@v{digest[:_HASH_PREFIX_LEN]}"
    if name not in registry.renderers:  # same name => same content; reload is a no-op
        registry.register_renderer(name, _template_renderer(package, role, source), source=source)
    return name


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
            return fh.read(), None
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
def _read_settings(path: str) -> dict[str, Any]:
    import yaml

    for fn in ("settings.yaml", "settings.yml"):
        cand = os.path.join(path, fn)
        if os.path.exists(cand):
            with open(cand, "r", encoding="utf-8") as fh:
                loaded = yaml.safe_load(fh) or {}
            if not isinstance(loaded, dict):
                raise ValueError(f"dotctx settings must be a YAML mapping: {cand!r}")
            return loaded
    raise FileNotFoundError(f"no settings.yaml in dotctx dir: {path!r}")


def _default_name(path: str) -> str:
    base = os.path.basename(os.path.normpath(path))
    return base[:-4] if base.endswith(".ctx") else base


def load_rich_dotctx(path: str, *, registry: Registry = DEFAULT_REGISTRY) -> RichDotctx:
    """Load a rich ``.ctx`` package: register renderers, brain, expectations."""
    settings = _read_settings(path)
    unknown = sorted(set(settings) - _ALLOWED_SETTINGS)
    if unknown:
        raise ValueError(
            f"unknown settings keys in {path!r}: {', '.join(unknown)} "
            f"(allowed: {', '.join(sorted(_ALLOWED_SETTINGS))})"
        )

    raw_name = settings.get("name")
    package = raw_name if isinstance(raw_name, str) and raw_name else _default_name(path)

    system_src, user_src = _read_templates(path)
    renderer_names: dict[str, str] = {}
    system_render: Optional[str] = None
    user_render: Optional[str] = None
    if system_src is not None:
        system_render = _register_template(registry, package, "system", system_src)
        renderer_names["system"] = system_render
    if user_src is not None:
        user_render = _register_template(registry, package, "user", user_src)
        renderer_names["user"] = user_render

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

    scope = ContextScope(settings["context"]) if settings.get("context") else ContextScope.LOCAL
    brain = Brain(
        name=package,
        model=settings.get("model", "claude-sonnet-4"),  # @effort suffixes pass through untouched
        system="",
        reply_schema=reply_schema,
        tools=tools,
        temperature=settings.get("temperature"),
        max_rounds=settings.get("max_rounds") or settings.get("maxRounds"),
        is_agent=bool(settings.get("agent", False)),
        sub_contract=_sub_from(settings.get("sub")),
        context_scope=scope,
        system_render=system_render,
        user_render=user_render,
        max_tokens=settings.get("max_tokens") or settings.get("maxTokens"),
    )
    brain = registry.register_brain(brain)

    return RichDotctx(
        brain=brain,
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
    "parse_schema_pyi",
    "parse_tools_pyi",
]
