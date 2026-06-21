"""Composable prompts via registered renderers (design: docs/design/prompt-fragments.md).

A renderer is a pure ``Context -> str`` registered by name (like a pure). A
Reasoner names one via ``system_render``; ``rendered_reasoner_for`` projects a Context
from the invoke value and returns a derived Reasoner whose ``system`` is the
rendered string. ``Context`` is the v1 projection: the invoke value if it is a
mapping (the agent-loop payload ``{"input":..., "trace":...}`` already is one),
else ``{"value": value}``. Richer ContextScope/session projection is deferred.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol

from .dotctx import Reasoner
from .registry import DEFAULT_REGISTRY, RendererEntry

Context = Mapping[str, Any]


class Fragment(Protocol):
    """Structural type for prompt fragments — anything that renders a Context to
    a string. For annotations only; ``fragments()`` auto-lifts by matching the
    concrete dataclasses in ``_FRAGMENT_TYPES``, not this Protocol."""

    def render(self, ctx: Context) -> str: ...


def register_renderer(name: str, fn: Callable[[Context], str]) -> RendererEntry:
    return DEFAULT_REGISTRY.register_renderer(name, fn)


def get_renderer(name: str) -> Callable[[Context], str]:
    return DEFAULT_REGISTRY.get_renderer(name)


def renderer(name: str) -> Callable[[Callable[[Context], str]], Callable[[Context], str]]:
    """Decorator: register a top-level ``def f(ctx) -> str`` as a renderer. Its
    source is what gets hashed for §6.4 drift, exactly like ``@pure``."""
    def deco(fn: Callable[[Context], str]) -> Callable[[Context], str]:
        register_renderer(name, fn)
        return fn
    return deco


def project_context(value: Any) -> dict[str, Any]:
    """v1 Context projection at the invoke boundary."""
    return dict(value) if isinstance(value, Mapping) else {"value": value}


def render_system(reasoner: Reasoner, ctx: Context) -> str:
    if reasoner.system_render is not None:
        return DEFAULT_REGISTRY.get_renderer(reasoner.system_render)(ctx)
    return reasoner.system


def render_user(reasoner: Reasoner, ctx: Context) -> Optional[str]:
    """The rendered user turn, or ``None`` when the reasoner names no user renderer
    (callers fall back to the value-as-JSON user turn)."""
    if reasoner.user_render is None:
        return None
    return DEFAULT_REGISTRY.get_renderer(reasoner.user_render)(ctx)


def rendered_user_for(reasoner: Reasoner, value: Any) -> Optional[str]:
    if reasoner.user_render is None:
        return None
    return render_user(reasoner, project_context(value))


def _with_rendered_system(reasoner: Reasoner, system: str) -> Reasoner:
    return Reasoner(
        name=reasoner.name, model=reasoner.model, system=system,
        reply_schema=reasoner.reply_schema, tools=reasoner.tools,
        temperature=reasoner.temperature, max_rounds=reasoner.max_rounds,
        is_agent=reasoner.is_agent, sub_contract=reasoner.sub_contract,
        context_scope=reasoner.context_scope, system_render=None,
        user_render=reasoner.user_render, max_tokens=reasoner.max_tokens,
    )


def rendered_reasoner_for(reasoner: Reasoner, value: Any) -> Reasoner:
    """The invoke seam: a no-renderer reasoner passes through identically; a
    renderer-bearing reasoner becomes a derived reasoner with the rendered system.
    ``user_render`` rides along — the LLM caller renders the user turn via
    :func:`rendered_user_for` against the same value."""
    if reasoner.system_render is None:
        return reasoner
    return _with_rendered_system(reasoner, render_system(reasoner, project_context(value)))


@dataclass(frozen=True)
class Lift:
    text: str
    def render(self, ctx: Context) -> str: return self.text


@dataclass(frozen=True)
class Ask:
    key: str
    fmt: Callable[[Any], str] = str
    def render(self, ctx: Context) -> str: return self.fmt(ctx.get(self.key, ""))


@dataclass(frozen=True)
class Concat:
    parts: tuple[Fragment, ...]
    def render(self, ctx: Context) -> str: return "".join(p.render(ctx) for p in self.parts)


@dataclass(frozen=True)
class Under:
    project: Callable[[Context], Context]
    body: Fragment
    def render(self, ctx: Context) -> str: return self.body.render(self.project(ctx))


@dataclass(frozen=True)
class Map:
    body: Fragment
    fn: Callable[[str], str]
    def render(self, ctx: Context) -> str: return self.fn(self.body.render(ctx))


_FRAGMENT_TYPES = (Lift, Ask, Concat, Under, Map)


def fragments(*parts: Any) -> Concat:
    return Concat(tuple(p if isinstance(p, _FRAGMENT_TYPES) else Lift(p) for p in parts))


__all__ = [
    "Context", "Fragment", "register_renderer", "get_renderer", "renderer",
    "project_context", "render_system", "rendered_reasoner_for",
    "render_user", "rendered_user_for",
    "Lift", "Ask", "Concat", "Under", "Map", "fragments",
]
