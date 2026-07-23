"""Dependency metadata helpers for bundle-sourced pures."""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from . import _env
from .ir import canonical_json

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:
    _tomllib = None

_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PYTHON_MAJOR_MINOR = re.compile(
    r"^\s*(?:~=|==|!=|<=|>=|<|>|===)?\s*(\d+)\.(\d+)(?:\.\d+)?"
)
_PEP723_ALLOWED_KEYS = frozenset({"dependencies", "requires-python", "tool"})


def _normalized_deps(deps: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(deps)))


def native_dep_grants(explicit: Iterable[str] | str | None = None) -> frozenset[str]:
    """Return pure names granted permission to use the native dependency tier."""
    raw = explicit
    if raw is None:
        raw = _env.get(_env.JULEP_PURE_NATIVE_DEPS, "")
    items: Iterable[str]
    if isinstance(raw, str):
        items = raw.split(",")
    else:
        items = raw
    return frozenset(item.strip() for item in items if item.strip())


def parse_pep723(source: str) -> tuple[tuple[str, ...], str | None]:
    """Return canonical PEP 723 dependencies and raw requires-python metadata."""
    lines = source.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index] != "# /// script":
            index += 1
            continue

        if blocks:
            raise ValueError("PEP 723 metadata must contain at most one script block")

        content: list[str] = []
        index += 1
        while index < len(lines) and lines[index] != "# ///":
            line = lines[index]
            if line.startswith("# "):
                content.append(line[2:])
            elif line.startswith("#"):
                content.append(line[1:])
            else:
                raise ValueError("malformed PEP 723 script block: content line is not a comment")
            index += 1

        if index >= len(lines):
            raise ValueError("malformed PEP 723 script block: missing closing '# ///'")
        blocks.append("\n".join(content))
        index += 1

    if not blocks:
        return (), None

    if _tomllib is None:
        raise RuntimeError("PEP 723 parsing requires Python 3.11 or newer")

    try:
        metadata = _tomllib.loads(blocks[0])
    except ValueError as e:
        raise ValueError(f"malformed PEP 723 script block TOML: {e}") from e

    unknown_keys = set(metadata) - _PEP723_ALLOWED_KEYS
    if unknown_keys:
        formatted = ", ".join(repr(key) for key in sorted(unknown_keys))
        raise ValueError(f"malformed PEP 723 script block: unknown key(s): {formatted}")

    raw_deps = metadata.get("dependencies", [])
    if not isinstance(raw_deps, list) or not all(isinstance(dep, str) for dep in raw_deps):
        raise ValueError("malformed PEP 723 script block: dependencies must be a list of strings")

    requires_python = metadata.get("requires-python")
    if requires_python is not None and not isinstance(requires_python, str):
        raise ValueError("malformed PEP 723 script block: requires-python must be a string")

    tool = metadata.get("tool")
    if tool is not None and not isinstance(tool, dict):
        raise ValueError("malformed PEP 723 script block: tool must be a table")

    if raw_deps or requires_python is not None:
        try:
            from packaging.requirements import InvalidRequirement, Requirement
            from packaging.specifiers import InvalidSpecifier, SpecifierSet
        except ImportError as e:
            raise RuntimeError(
                "strict PEP 723 validation requires the 'packaging' package"
            ) from e

        for dep in raw_deps:
            try:
                Requirement(dep)
            except InvalidRequirement as e:
                raise ValueError(f"PEP 723 dependency is not valid PEP 508: {dep!r}") from e

        if requires_python is not None:
            try:
                SpecifierSet(requires_python)
            except InvalidSpecifier as e:
                raise ValueError(
                    "PEP 723 requires-python is not a valid version specifier: "
                    f"{requires_python!r}"
                ) from e

    return _normalized_deps(raw_deps), requires_python


def _python_major_minor(requires_python: str | None) -> str | None:
    if requires_python is None:
        return None
    match = _PYTHON_MAJOR_MINOR.match(requires_python)
    if match is None:
        return None
    return f"{match.group(1)}.{match.group(2)}"


def _base_component_digest(base_component: bytes | str) -> str:
    if isinstance(base_component, str):
        if _HEX_SHA256.fullmatch(base_component):
            return base_component
        raw = base_component.encode("utf-8")
    else:
        raw = base_component
    return hashlib.sha256(raw).hexdigest()


def env_hash(
    deps: Sequence[str],
    requires_python: str | None,
    base_component: bytes | str,
) -> str:
    """Return sha256 over canonical dep env JSON.

    ``base_component`` may be raw component bytes or a lowercase 64-hex sha256
    digest. Other strings are hashed as UTF-8 bytes.
    """
    payload = {
        "deps": list(_normalized_deps(deps)),
        "requiresPython": _python_major_minor(requires_python),
        "baseComponent": _base_component_digest(base_component),
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _base_wasm_path() -> Path:
    return Path(__file__).parent / "execution" / "_wasm" / "executor.wasm"


def base_component_hash() -> str:
    """Return sha256 hex of the vendored wasm executor component."""
    return hashlib.sha256(_base_wasm_path().read_bytes()).hexdigest()
