"""Yglu-evaluated ``settings.yaml`` with an explicit ``$env`` binding.

mem-mcp's ``.ctx`` settings use yglu expressions — universally
``!? $env.get("VAR", default)`` — for env-dependent model/round config. To keep
freezes deterministic, ``$env`` never reads the ambient process environment
here: callers pass the mapping (the Julep env profile), and ``os.environ`` is
swapped for exactly that mapping while yglu evaluates. Load/CLI-time only —
the swap is process-global and not thread-safe.

Requires the ``julep[yglu]`` extra; evaluating a tagged file
without yglu is a hard, actionable error (G-8: no silent fallback).

Deployed workers: ``$env`` never reads the ambient process environment — with
no binding, tagged settings evaluate to their *defaults*. A Temporal worker
that imports ``.ctx`` packages must call :func:`set_default_env` with the same
env profile the artifact was frozen against (``julep.toml`` ``[env.<name>.vars]``)
*before* those imports, or its registry can disagree with the frozen identity.
Persisting the resolved reasoner config into the artifact (so workers need no
manual binding) is deferred to the deployment phase.
"""
from __future__ import annotations

import io
import os
import re
from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional

_TAG_RE = re.compile(r"!\?|!\(\)|!if\b|!for\b|!concat\b|!merge\b")
_YGLU_TAG_SUFFIXES = frozenset({"?", "()", "if", "for", "concat", "merge"})
_DEFAULT_ENV: Optional[Mapping[str, str]] = None


def has_yglu_tags(text: str) -> bool:
    """True when ``text`` carries a yglu tag at an actual YAML tag position.

    Detection is structural (scanner tokens), so punctuation inside scalars —
    ``system: "Really!?"`` — is content, not a tag. Text the scanner rejects
    falls back to the regex: an unscannable file fails to load either way, and
    the tagged route reports the more useful error.
    """
    import yaml

    try:
        return any(
            isinstance(token, yaml.TagToken)
            and token.value[0] == "!"
            and token.value[1] in _YGLU_TAG_SUFFIXES
            for token in yaml.scan(text)
        )
    except yaml.YAMLError:
        return _TAG_RE.search(text) is not None


def set_default_env(env: Optional[Mapping[str, str]]) -> None:
    global _DEFAULT_ENV
    _DEFAULT_ENV = None if env is None else dict(env)


def default_env() -> Optional[Mapping[str, str]]:
    return _DEFAULT_ENV


def _import_yglu() -> Any:
    from yglu import builder

    return builder


@contextmanager
def _exact_environ(env: Mapping[str, str]) -> Iterator[None]:
    saved = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update({**env, "YGLU_ENABLE_ENV": "1"})
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def _to_plain(value: Any) -> Any:
    """Force yglu's lazy tree into plain Python containers.

    yglu expressions evaluate on *access* (``Mapping.items()`` /
    ``Sequence.__iter__``), so nested nodes handed out of ``load_settings``
    would otherwise read whatever ``os.environ`` holds later. Walking the
    whole tree inside the environ swap freezes every ``$env`` read against
    exactly the declared mapping (mirrors mem-mcp's loader).
    """
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    return value


def load_settings(
    text: str, *, env: Optional[Mapping[str, str]], filepath: str
) -> dict[str, Any]:
    try:
        builder = _import_yglu()
    except ImportError as exc:
        raise ImportError(
            "settings.yaml uses yglu expressions; install julep[yglu]"
        ) from exc
    binding = dict(env) if env is not None else dict(default_env() or {})
    with _exact_environ(binding):
        result = builder.build(io.StringIO(text), filepath=filepath)
        settings: Any = _to_plain(result) if result else {}
    if not isinstance(settings, dict):
        raise ValueError(f"settings must be a YAML mapping: {filepath!r}")
    return settings


__all__ = ["default_env", "has_yglu_tags", "load_settings", "set_default_env"]
