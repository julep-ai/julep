"""Closed standard pure family emitted by composable-agents frontends.

These pures are registered at package import so frozen artifacts can reference a
small, wire-format-stable glue vocabulary instead of ad hoc closures.
"""

from __future__ import annotations

from typing import Any

from .registry import DEFAULT_REGISTRY


def std_merge(value: Any, *, fields: list[str] | None = None) -> dict[str, Any]:
    """Wire-format-stable std.merge; body frozen once any artifact references it.

    With no static args, ``value`` is the binary pair-input layout used by ``|``:
    ``[left, right]``. With ``fields``, ``value`` is an env record and each named
    env field is merged in list order. In both layouts, later dictionaries win.
    Deliberate behavior changes require registering a new std name.
    """
    if fields is None:
        left, right = value
        pair_merged = dict(left)
        pair_merged.update(right)
        return pair_merged

    projected: dict[str, Any] = {}
    for field in fields:
        projected.update(value[field])
    return projected


def std_pluck(value: Any, *, key: str) -> Any:
    """Wire-format-stable std.pluck; body frozen once any artifact references it.

    Projects one key from the flowing record. Deliberate behavior changes
    require registering a new std name.
    """
    return value[key]


def std_init(value: Any, *, key: str) -> dict[str, Any]:
    """Wire-format-stable std.init; body frozen once any artifact references it.

    Starts an env record by wrapping the raw flowing value under ``key``.
    Deliberate behavior changes require registering a new std name.
    """
    return {key: value}


def std_assign(value: Any, *, key: str) -> dict[str, Any]:
    """Wire-format-stable std.assign; body frozen once any artifact references it.

    Extends an existing env record from a fixed pair-input layout ``[env, item]``.
    This is distinct from std.init and never sniffs the flowing value to choose
    env-entry vs env-extend behavior. Deliberate behavior changes require
    registering a new std name.
    """
    env, item = value
    copied = dict(env)
    copied[key] = item
    return copied


def std_pack(value: Any, *, fields: dict[str, Any]) -> dict[str, Any]:
    """Wire-format-stable std.pack; body frozen once any artifact references it.

    Builds a named record for closure conversion. Each output name maps to one
    selector: ``{"field": "source"}`` copies a field from the flowing input,
    ``{"input": true}`` copies the whole flowing input, and ``{"const": value}``
    embeds a JSON static arg value. Deliberate behavior changes require
    registering a new std name.
    """
    packed: dict[str, Any] = {}
    for name, selector in fields.items():
        if isinstance(selector, dict) and set(selector) == {"field"}:
            packed[name] = value[selector["field"]]
        elif isinstance(selector, dict) and set(selector) == {"input"} and selector["input"] is True:
            packed[name] = value
        elif isinstance(selector, dict) and set(selector) == {"const"}:
            packed[name] = selector["const"]
        else:
            raise ValueError(f"std.pack invalid selector for field {name!r}")
    return packed


def std_unpack(value: Any, *, fields: dict[str, str]) -> dict[str, Any]:
    """Wire-format-stable std.unpack; body frozen once any artifact references it.

    Unpacks a named closure-conversion record. ``fields`` maps output env names
    to packed-record field names. Deliberate behavior changes require
    registering a new std name.
    """
    unpacked: dict[str, Any] = {}
    for name, source in fields.items():
        unpacked[name] = value[source]
    return unpacked


def std_bind(value: Any, *, consts: dict[str, Any]) -> dict[str, Any]:
    """Wire-format-stable std.bind; body frozen once any artifact references it.

    Adds static JSON constants to the flowing input. If a const key is already
    present in the flowing input, raises a deterministic collision error.
    Deliberate behavior changes require registering a new std name.
    """
    collisions = [key for key in sorted(consts) if key in value]
    if collisions:
        raise ValueError("std.bind key collision: " + ", ".join(collisions))

    merged = dict(value)
    for key in sorted(consts):
        merged[key] = consts[key]
    return merged


DEFAULT_REGISTRY.register_pure("std.merge", std_merge)
DEFAULT_REGISTRY.register_pure("std.pluck", std_pluck)
DEFAULT_REGISTRY.register_pure("std.init", std_init)
DEFAULT_REGISTRY.register_pure("std.assign", std_assign)
DEFAULT_REGISTRY.register_pure("std.pack", std_pack)
DEFAULT_REGISTRY.register_pure("std.unpack", std_unpack)
DEFAULT_REGISTRY.register_pure("std.bind", std_bind)
