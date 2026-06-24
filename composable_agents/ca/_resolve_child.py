"""Run inside the user's interpreter (separate process). Imports user modules,
finds the named agent, prints {ir, name} or {error} as JSON to stdout."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any


def _discover_module_names(root: str, src: list[str]) -> list[str]:
    names: list[str] = []
    root_path = Path(root)
    for entry in src:
        base = root_path / entry
        for py in [base] if base.is_file() else base.rglob("*.py"):
            if py.name == "__init__.py":
                continue
            rel = py.relative_to(root_path).with_suffix("")
            names.append(".".join(rel.parts))
    return names


def main() -> int:
    payload = json.loads(sys.argv[1])
    root: str = payload["root"]
    src: list[str] = payload["src"]
    target: str = payload["name"]
    sys.path.insert(0, root)
    from composable_agents.define import FlowLike  # type: ignore[attr-defined]

    found: FlowLike[Any, Any] | None = None
    for modname in _discover_module_names(root, src):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        for attr in vars(mod).values():
            if isinstance(attr, FlowLike) and getattr(attr, "name", None) == target:
                found = attr
                break
        if found is not None:
            break

    if found is None:
        print(json.dumps({"error": f"agent {target!r} not found"}))
        return 0
    node = found.to_ir()
    print(json.dumps({"ir": node.to_json(), "name": target}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
