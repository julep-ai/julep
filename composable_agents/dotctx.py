"""dotctx adapter (blueprint §3.2, the leaf that turns a prompt dir into a brain).

A *dotctx* is a directory describing one model call: a ``settings.yaml`` (model,
temperature, round bound, granted tools), a system prompt, and an optional reply
schema. This module reads that layout into a :class:`Brain` (registered by name,
the same way pure functions are registered) and lowers it to IR. The lowering is
where the round bound becomes *shape*, faithfully to the blueprint:

* a **bounded** ``max_rounds`` (>= 1) -> ``iter_up_to`` (Feedback): the model gets
  that many passes and no more;
* an **open-ended** brain (``agent: true``, no finite bound) -> ``app``
  (Agent): the costly, continuation-owning shape, used deliberately;
* a dotctx marked as a child (``sub:``) -> ``sub`` (a Temporal child
  workflow behind the Joined firewall, the ``to_dbos_agent`` mapping);
* otherwise a single ``think`` leaf (Pipeline).

Reply schema and granted tools ride on the :class:`Brain`; ``invokeBrain`` in
:mod:`composable_agents.execution.activities` reads them at run time. Context is
declared on the leaf, never ambient.
"""

from __future__ import annotations

import os
import types
from dataclasses import dataclass
from typing import (
    Any,
    Literal,
    Optional,
    Sequence,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)
from typing import NotRequired, Required  # type: ignore[attr-defined]

from .dsl import app, iter_up_to, sub, think
from .ir import ContextPolicy, Node, SubContract
from .kinds import ContextScope, Shape, SummaryPolicy
from .registry import DEFAULT_REGISTRY

_REPLY_UNSET = object()
_SUPPORTED_REPLY_FORMS = "pydantic v2 model with model_json_schema() or TypedDict"


def _unsupported_reply_type(value: object) -> TypeError:
    return TypeError(
        f"unsupported reply= value {value!r}; supported forms: {_SUPPORTED_REPLY_FORMS}"
    )


def _annotation_to_schema(annotation: Any) -> dict[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if getattr(origin, "__name__", None) in ("Required", "NotRequired"):
        return _annotation_to_schema(args[0])

    if annotation is Any:
        return {}
    if annotation is str:
        return {"type": "string"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is type(None):
        return {"type": "null"}
    if origin is Literal:
        return {"enum": list(args)}
    if origin in (Union, types.UnionType):
        return {"anyOf": [_annotation_to_schema(arg) for arg in args]}
    if origin is list:
        item_schema = _annotation_to_schema(args[0]) if args else {}
        return {"type": "array", "items": item_schema}
    if origin is dict:
        if len(args) == 2 and args[0] is str:
            return {"type": "object", "additionalProperties": _annotation_to_schema(args[1])}
        raise TypeError(f"unsupported dict annotation {annotation!r}; use dict[str, T]")
    if is_typeddict(annotation):
        return _typeddict_to_schema(annotation)

    raise TypeError(
        f"unsupported reply TypedDict field annotation {annotation!r}; "
        f"supported forms: {_SUPPORTED_REPLY_FORMS}"
    )


def _typeddict_to_schema(reply: Any) -> dict[str, Any]:
    try:
        annotations = get_type_hints(reply, include_extras=True)
    except Exception as exc:
        raise _unsupported_reply_type(reply) from exc

    required_keys = set(getattr(reply, "__required_keys__", frozenset()))
    properties = {
        key: _annotation_to_schema(annotation)
        for key, annotation in annotations.items()
    }
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    required: list[str] = []
    for key, annotation in annotations.items():
        origin = get_origin(annotation)
        if origin is Required:
            required.append(key)
        elif origin is NotRequired:
            continue
        elif key in required_keys:
            required.append(key)
    if required:
        schema["required"] = required
    return schema


def _reply_to_schema(reply: Any) -> dict[str, Any]:
    model_json_schema = getattr(reply, "model_json_schema", None)
    if callable(model_json_schema):
        schema = model_json_schema()
        if not isinstance(schema, dict):
            raise TypeError("reply.model_json_schema() must return a dict")
        return cast(dict[str, Any], schema)

    if is_typeddict(reply):
        return _typeddict_to_schema(reply)

    raise _unsupported_reply_type(reply)


@dataclass(frozen=True, init=False)
class Brain:
    """A resolved model-call configuration, addressed by ``name``."""

    name: str
    model: str
    system: str = ""
    reply_schema: Optional[dict[str, Any]] = None
    tools: tuple[str, ...] = ()           # toolref keys this brain may call
    temperature: Optional[float] = None
    max_rounds: Optional[int] = None      # >=1 bounded; None/0 open-ended
    is_agent: bool = False                # explicit open-ended app
    sub_contract: Optional[SubContract] = None  # marks a child workflow
    context_scope: ContextScope = ContextScope.LOCAL
    system_render: Optional[str] = None   # registered renderer name (a string); None => use `system`
    user_render: Optional[str] = None     # registered renderer name for the user turn
    max_tokens: Optional[int] = None      # forwarded to the provider call when set

    def __init__(
        self,
        name: str,
        model: str,
        system: str = "",
        reply_schema: Optional[dict[str, Any]] = None,
        tools: Sequence[str] = (),
        temperature: Optional[float] = None,
        max_rounds: Optional[int] = None,
        is_agent: bool = False,
        sub_contract: Optional[SubContract] = None,
        context_scope: ContextScope = ContextScope.LOCAL,
        system_render: Optional[str] = None,
        user_render: Optional[str] = None,
        max_tokens: Optional[int] = None,
        *,
        reply: Any = _REPLY_UNSET,
    ) -> None:
        if reply is not _REPLY_UNSET:
            if reply_schema is not None:
                raise ValueError("reply= and reply_schema= are mutually exclusive")
            reply_schema = _reply_to_schema(reply)

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "system", system)
        object.__setattr__(self, "reply_schema", reply_schema)
        object.__setattr__(self, "tools", tuple(tools))
        object.__setattr__(self, "temperature", temperature)
        object.__setattr__(self, "max_rounds", max_rounds)
        object.__setattr__(self, "is_agent", is_agent)
        object.__setattr__(self, "sub_contract", sub_contract)
        object.__setattr__(self, "context_scope", context_scope)
        object.__setattr__(self, "system_render", system_render)
        object.__setattr__(self, "user_render", user_render)
        object.__setattr__(self, "max_tokens", max_tokens)


_BRAINS: dict[str, Brain] = DEFAULT_REGISTRY.brains


def register_brain(brain: Brain) -> Brain:
    return DEFAULT_REGISTRY.register_brain(brain)


def get_brain(name: str) -> Brain:
    return DEFAULT_REGISTRY.get_brain(name)


def list_brains() -> list[str]:
    return DEFAULT_REGISTRY.list_brains()


def registered_brains() -> list[str]:
    return DEFAULT_REGISTRY.list_brains()


# --------------------------------------------------------------------------- #
# Parsing a dotctx directory / dict into a Brain.
# --------------------------------------------------------------------------- #
def _sub_from(d: Optional[dict[str, Any]]) -> Optional[SubContract]:
    if not d:
        return None
    shape = Shape(d["shape"])
    sp = SummaryPolicy(d["summaryPolicy"]) if d.get("summaryPolicy") else (
        SummaryPolicy(d["summary_policy"]) if d.get("summary_policy") else None
    )
    return SubContract(shape=shape, summary_policy=sp)


def brain_from_settings(settings: dict[str, Any], *, name: Optional[str] = None,
                        base_dir: Optional[str] = None) -> Brain:
    """Build (and register) a :class:`Brain` from a settings mapping.

    ``base_dir`` lets ``system_file`` / ``schema_file`` resolve relative paths;
    omit it to use only inline ``system`` / ``reply_schema`` values.
    """
    nm = name or settings.get("name")
    if not nm:
        raise ValueError("dotctx settings need a 'name'")

    system = settings.get("system", "")
    if not system and settings.get("system_file") and base_dir:
        path = os.path.join(base_dir, settings["system_file"])
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                system = fh.read()

    reply_schema = settings.get("reply_schema") or settings.get("replySchema")
    if reply_schema is None and settings.get("schema_file") and base_dir:
        import json
        path = os.path.join(base_dir, settings["schema_file"])
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                reply_schema = json.load(fh)

    scope = ContextScope(settings["context"]) if settings.get("context") else ContextScope.LOCAL

    brain = Brain(
        name=nm,
        model=settings.get("model", "claude-sonnet-4"),
        system=system,
        reply_schema=reply_schema,
        tools=tuple(settings.get("tools", []) or []),
        temperature=settings.get("temperature"),
        max_rounds=settings.get("max_rounds") or settings.get("maxRounds"),
        is_agent=bool(settings.get("agent", False)),
        sub_contract=_sub_from(settings.get("sub")),
        context_scope=scope,
        system_render=settings.get("system_render") or settings.get("systemRender"),
        user_render=settings.get("user_render") or settings.get("userRender"),
        max_tokens=settings.get("max_tokens") or settings.get("maxTokens"),
    )
    return register_brain(brain)


# Rich-layout markers: any of these turns the package over to dotctx_rich
# (which requires the ``composable-agents[dotctx]`` extra). One loader, one
# format — the minimal settings-only layout below stays unchanged.
_RICH_MARKERS = ("prompt.j2", "messages", "schema.pyi", "tools.pyi")


def is_rich_dotctx(path: str) -> bool:
    return any(os.path.exists(os.path.join(path, m)) for m in _RICH_MARKERS)


def load_dotctx(path: str) -> Brain:
    """Read ``<path>/settings.yaml`` (or ``settings.yml``) into a Brain.

    The brain's name defaults to the directory name when ``settings.yaml`` omits
    one, so a dotctx at ``brains/planner/`` registers as ``planner``. Packages
    carrying rich-layout files (``prompt.j2``, ``messages/``, ``schema.pyi``,
    ``tools.pyi``) are loaded by :mod:`composable_agents.dotctx_rich`.
    """
    if is_rich_dotctx(path):
        from . import dotctx_rich  # hard ImportError without the [dotctx] extra

        return dotctx_rich.load_rich_dotctx(path).brain

    try:
        import yaml
    except ModuleNotFoundError as e:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load a dotctx from disk") from e

    settings_path = None
    for fn in ("settings.yaml", "settings.yml"):
        cand = os.path.join(path, fn)
        if os.path.exists(cand):
            settings_path = cand
            break
    if settings_path is None:
        raise FileNotFoundError(f"no settings.yaml in dotctx dir: {path!r}")

    with open(settings_path, "r", encoding="utf-8") as fh:
        settings = yaml.safe_load(fh) or {}
    default_name = os.path.basename(os.path.normpath(path))
    return brain_from_settings(settings, name=settings.get("name", default_name),
                               base_dir=path)


# --------------------------------------------------------------------------- #
# Lowering a Brain to IR (the shape-bearing step).
# --------------------------------------------------------------------------- #
def brain_to_flow(brain: Brain, *, ctx: Optional[ContextPolicy] = None) -> Node:
    """Lower a registered brain to the IR node its round policy implies.

    Sub before agent before bounded loop before single call, so an explicitly
    declared child contract always wins.
    """
    policy = ctx or ContextPolicy(scope=brain.context_scope)

    if brain.sub_contract is not None:
        return sub(brain.name, brain.sub_contract,
                   summary_policy=brain.sub_contract.summary_policy)

    if brain.is_agent or (brain.max_rounds is not None and brain.max_rounds <= 0):
        # Open-ended controller loop. The brain name is the controller ref.
        # Transcript policy: an explicit ctx wins; else derive it from the
        # brain's declared context scope. LOCAL adds no ctx key (hash-stable).
        app_ctx = ctx
        if app_ctx is None and brain.context_scope in (
            ContextScope.SUMMARY,
            ContextScope.WHOLE_SESSION,
        ):
            app_ctx = ContextPolicy(scope=brain.context_scope)
        return app(brain.name, ctx=app_ctx)

    if brain.max_rounds is not None and brain.max_rounds >= 1:
        # Bounded refinement loop -> Feedback.
        return iter_up_to(brain.max_rounds, think(brain.name, ctx=policy))

    # Default: a single model call -> Pipeline.
    return think(brain.name, ctx=policy)


def dotctx_flow(path: str, *, ctx: Optional[ContextPolicy] = None) -> Node:
    """Convenience: :func:`load_dotctx` then :func:`brain_to_flow`."""
    return brain_to_flow(load_dotctx(path), ctx=ctx)
