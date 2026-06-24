"""Run inside the user's interpreter (separate process). Imports user modules,
finds the named agent, and emits ``{ir, name}`` or ``{error}`` as JSON.

The JSON result is written between two unique sentinel markers on stdout so the
parent never has to guess which line is the payload — arbitrary module-level
``print`` calls from user code cannot corrupt or hijack parsing.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

# Unique markers delimiting the JSON payload on stdout. The parent extracts the
# text between them rather than relying on "json is the last line".
_BEGIN = "__CA_RESOLVE_BEGIN__"
_END = "__CA_RESOLVE_END__"


def _discover_modules(root: str, src: list[str]) -> list[tuple[str, str]]:
    """Yield ``(sys_path_entry, dotted_module_name)`` pairs for every src file.

    Module names are computed relative to their *src entry* (not the repo root)
    and that entry is what goes on ``sys.path`` — so a ``src/`` layout file
    ``src/myapp/agents.py`` imports as ``myapp.agents`` with ``src/`` on the
    path, and intra-package imports (``from myapp.x import ...``) resolve.
    """
    root_path = Path(root)
    out: list[tuple[str, str]] = []
    for entry in src:
        base = root_path / entry
        # The directory whose contents become importable top-level modules.
        path_entry = str(base.parent if base.is_file() else base)
        files = [base] if base.is_file() else base.rglob("*.py")
        for py in files:
            if py.name == "__init__.py":
                continue
            anchor = base.parent if base.is_file() else base
            rel = py.relative_to(anchor).with_suffix("")
            out.append((path_entry, ".".join(rel.parts)))
    return out


def _emit(data: dict[str, Any]) -> None:
    sys.stdout.write(f"\n{_BEGIN}\n{json.dumps(data)}\n{_END}\n")
    sys.stdout.flush()


def main() -> int:
    payload = json.loads(sys.argv[1])
    root: str = payload["root"]
    src: list[str] = payload["src"]
    target: str = payload["name"]
    sys.path.insert(0, root)
    from composable_agents.define import FlowLike  # type: ignore[attr-defined]

    found: FlowLike[Any, Any] | None = None
    import_errors: list[str] = []
    for path_entry, modname in _discover_modules(root, src):
        if path_entry not in sys.path:
            sys.path.insert(0, path_entry)
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 - capture so we can surface it below.
            import_errors.append(f"{modname}: {type(exc).__name__}: {exc}")
            continue
        for attr in vars(mod).values():
            # @flow exposes a public ``.name``; Agent stores it on ``._name``.
            name = getattr(attr, "name", None) or getattr(attr, "_name", None)
            if isinstance(attr, FlowLike) and name == target:
                found = attr
                break
        if found is not None:
            break

    if found is None:
        msg = f"agent {target!r} not found"
        if import_errors:
            msg += "; import errors: " + " | ".join(import_errors)
        _emit({"error": msg})
        return 0
    node = found.to_ir()
    _emit({"ir": node.to_json(), "name": target})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
