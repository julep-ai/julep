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
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from .dsl import app, iter_up_to, sub, think
from .ir import ContextPolicy, Node, SubContract
from .kinds import ContextScope, Shape, SummaryPolicy
from .registry import DEFAULT_REGISTRY


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
    ) -> None:
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
    )
    return register_brain(brain)


def load_dotctx(path: str) -> Brain:
    """Read ``<path>/settings.yaml`` (or ``settings.yml``) into a Brain.

    The brain's name defaults to the directory name when ``settings.yaml`` omits
    one, so a dotctx at ``brains/planner/`` registers as ``planner``.
    """
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
        return app(brain.name)

    if brain.max_rounds is not None and brain.max_rounds >= 1:
        # Bounded refinement loop -> Feedback.
        return iter_up_to(brain.max_rounds, think(brain.name, ctx=policy))

    # Default: a single model call -> Pipeline.
    return think(brain.name, ctx=policy)


def dotctx_flow(path: str, *, ctx: Optional[ContextPolicy] = None) -> Node:
    """Convenience: :func:`load_dotctx` then :func:`brain_to_flow`."""
    return brain_to_flow(load_dotctx(path), ctx=ctx)
