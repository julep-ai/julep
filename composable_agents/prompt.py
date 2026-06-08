"""Composable prompts via registered renderers (design: docs/design/prompt-fragments.md).

A renderer is a pure ``Context -> str`` registered by name (like a pure). A
Brain names one via ``system_render``; ``rendered_brain_for`` projects a Context
from the invoke value and returns a derived Brain whose ``system`` is the
rendered string. ``Context`` is the v1 projection: the invoke value if it is a
mapping (the agent-loop payload ``{"input":..., "trace":...}`` already is one),
else ``{"value": value}``. Richer ContextScope/session projection is deferred.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .dotctx import Brain
from .registry import DEFAULT_REGISTRY

Context = Mapping[str, Any]


def register_renderer(name: str, fn: Callable[[Context], str]):
    return DEFAULT_REGISTRY.register_renderer(name, fn)


def get_renderer(name: str) -> Callable[[Context], str]:
    return DEFAULT_REGISTRY.get_renderer(name)


def renderer(name: str):
    """Decorator: register a top-level ``def f(ctx) -> str`` as a renderer. Its
    source is what gets hashed for §6.4 drift, exactly like ``@pure``."""
    def deco(fn: Callable[[Context], str]) -> Callable[[Context], str]:
        register_renderer(name, fn)
        return fn
    return deco


def project_context(value: Any) -> dict[str, Any]:
    """v1 Context projection at the invoke boundary."""
    return dict(value) if isinstance(value, Mapping) else {"value": value}


def render_system(brain: Brain, ctx: Context) -> str:
    if brain.system_render is not None:
        return DEFAULT_REGISTRY.get_renderer(brain.system_render)(ctx)
    return brain.system


def _with_rendered_system(brain: Brain, system: str) -> Brain:
    return Brain(
        name=brain.name, model=brain.model, system=system,
        reply_schema=brain.reply_schema, tools=brain.tools,
        temperature=brain.temperature, max_rounds=brain.max_rounds,
        is_agent=brain.is_agent, sub_contract=brain.sub_contract,
        context_scope=brain.context_scope, system_render=None,
    )


def rendered_brain_for(brain: Brain, value: Any) -> Brain:
    """The invoke seam: a no-renderer brain passes through identically; a
    renderer-bearing brain becomes a derived brain with the rendered system."""
    if brain.system_render is None:
        return brain
    return _with_rendered_system(brain, render_system(brain, project_context(value)))


__all__ = [
    "Context", "register_renderer", "get_renderer", "renderer",
    "project_context", "render_system", "rendered_brain_for",
]
