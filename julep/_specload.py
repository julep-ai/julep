"""Import helpers for explicit ``module:attr`` callable specifications."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def resolve_spec(spec: str, *, what: str = "spec") -> Any:
    """Resolve a ``module:attr`` spec (whose attr may be dotted) to a callable."""
    module_name, sep, attr_path = spec.partition(":")
    if not sep or not module_name or not attr_path:
        raise ValueError(f"{what} spec must be 'module:attr', got {spec!r}")
    try:
        target: Any = import_module(module_name)
    except ImportError as exc:
        raise ValueError(f"cannot import {what} module {module_name!r}: {exc}") from exc
    for part in attr_path.split("."):
        try:
            target = getattr(target, part)
        except AttributeError as exc:
            raise ValueError(
                f"{what} {spec!r}: module {module_name!r} has no attribute {attr_path!r}"
            ) from exc
    if not callable(target):
        raise ValueError(f"{what} {spec!r} is not callable")
    return target


__all__ = ["resolve_spec"]
