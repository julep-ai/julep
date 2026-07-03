"""Run inside the user's interpreter (separate process). Imports user modules,
finds the named agent, and emits ``{ir, name}`` or ``{error}`` as JSON.

The JSON result is written between two unique sentinel markers on stdout so the
parent never has to guess which line is the payload — arbitrary module-level
``print`` calls from user code cannot corrupt or hijack parsing.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from composable_agents.typed import FlowLike

# Unique markers delimiting the JSON payload on stdout. The parent extracts the
# text between them rather than relying on "json is the last line".
_BEGIN = "__CA_RESOLVE_BEGIN__"
_END = "__CA_RESOLVE_END__"
_LOCAL_DEV_SIGNING_KEY = "0" * 64


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


@dataclass(frozen=True)
class _DiscoveryResult:
    found: FlowLike[Any, Any] | None
    modules: list[ModuleType]
    import_errors: list[str]


def _discover_agent(root: str, src: list[str], target: str) -> _DiscoveryResult:
    sys.path.insert(0, root)
    from composable_agents.typed import FlowLike

    found: FlowLike[Any, Any] | None = None
    modules: list[ModuleType] = []
    import_errors: list[str] = []
    for path_entry, modname in _discover_modules(root, src):
        if path_entry not in sys.path:
            sys.path.insert(0, path_entry)
        try:
            mod = importlib.import_module(modname)
        except Exception as exc:  # noqa: BLE001 - capture so we can surface it below.
            import_errors.append(f"{modname}: {type(exc).__name__}: {exc}")
            continue
        modules.append(mod)
        for attr in vars(mod).values():
            # @flow exposes a public ``.name``; Agent stores it on ``._name``.
            name = getattr(attr, "name", None) or getattr(attr, "_name", None)
            if isinstance(attr, FlowLike) and name == target:
                found = attr
                break
        if found is not None:
            break

    return _DiscoveryResult(found=found, modules=modules, import_errors=import_errors)


def _not_found_error(target: str, import_errors: list[str]) -> str:
    msg = f"agent {target!r} not found"
    if import_errors:
        msg += "; import errors: " + " | ".join(import_errors)
    return msg


def _freeze_agent(
    found: FlowLike[Any, Any],
    modules: list[ModuleType],
    cas: str,
    *,
    publish: bool = True,
    queue: Optional[str] = None,
) -> dict[str, Any]:
    from composable_agents.agent import Tool, snapshot_from_tools
    from composable_agents.cas import LocalDirCAS, cas_from_url
    from composable_agents.deploy import deploy
    from composable_agents.ir import toolref_key
    from composable_agents.validate import blocking

    tools_by_name: dict[str, Tool[Any, Any]] = {}
    for mod in modules:
        for attr in vars(mod).values():
            if isinstance(attr, Tool):
                tools_by_name[attr.name] = attr

    found_tools = getattr(found, "_tools", ())
    if isinstance(found_tools, (list, tuple)):
        for attr in found_tools:
            if isinstance(attr, Tool):
                tools_by_name[attr.name] = attr

    node = found.to_ir()
    selected_tools: list[Tool[Any, Any]] = []
    selected_names: set[str] = set()
    for ref in node.tool_refs():
        names = [toolref_key(ref)]
        ref_name = getattr(ref, "name", None)
        if isinstance(ref_name, str) and ref_name not in names:
            names.append(ref_name)
        for name in names:
            tool = tools_by_name.get(name)
            if tool is not None and tool.name not in selected_names:
                selected_tools.append(tool)
                selected_names.add(tool.name)
                break

    snapshot = snapshot_from_tools(selected_tools)
    # strict=False so we can surface the prod gap ourselves rather than letting
    # ValidationError abort before we can attach a human-readable summary. We
    # still REFUSE to publish/record a blocking deployment below.
    dep = deploy(node, snapshot, strict=False, queue=queue)
    bad = blocking(dep.diagnostics)
    if bad:
        return {"error": dep.prod_gap_summary()}

    pinned_pures = {
        key: value
        for key, value in dep.artifact_components["pureSourceHashes"].items()
        if isinstance(value, str)
    }
    result: dict[str, Any] = {
        "artifact_hash": dep.artifact_hash,
        "flow_json": dep.flow_json,
        "manifest_json": dep.manifest_json,
        "bundle_ref": dep.bundle_ref,
        "pinned_pures": pinned_pures,
    }
    dep_queue = getattr(dep, "queue", None)
    if dep_queue is not None:
        result["queue"] = dep_queue
    if not publish:
        # Read-only path (`ca status`): the artifact_hash is a cached_property of
        # artifact_components and needs no CAS mutation / S3 upload to compute.
        return result

    store = cas_from_url(cas) if cas.startswith("s3://") else LocalDirCAS(cas)
    if not cas.startswith("s3://"):
        os.environ.setdefault("CA_BUNDLE_SIGNING_KEY", _LOCAL_DEV_SIGNING_KEY)
    dep.publish(store)
    # publish() may rewrite bundle_ref (runtime refs present -> a list, else None).
    result["bundle_ref"] = dep.bundle_ref
    return result


def main() -> int:
    # The parent writes the request payload to stdin (not argv) so a large
    # ``ca run`` input cannot exceed the OS single-argument limit
    # (MAX_ARG_STRLEN, ~128 KiB on Linux). argv[1] is honored as a fallback for
    # any direct caller.
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    payload = json.loads(raw)
    root: str = payload["root"]
    src: list[str] = payload["src"]
    target: str = payload["name"]
    action = payload.get("action", "resolve")

    # Bind the ca env profile as the dotctx yglu default env BEFORE any user
    # module import: user code calling load_dotctx() at import time must see
    # exactly the declared vars (never this process's ambient environment).
    # The child owns the binding for its lifetime and exits.
    env_vars = payload.get("env_vars")
    if env_vars is not None:
        from composable_agents.dotctx_yglu import set_default_env

        set_default_env({str(k): str(v) for k, v in env_vars.items()})

    if action in ("freeze", "freeze_check"):
        try:
            result = _discover_agent(root, src, target)
            if result.found is None:
                _emit({"error": _not_found_error(target, result.import_errors)})
                return 0
            _emit(
                _freeze_agent(
                    result.found,
                    result.modules,
                    str(payload["cas"]),
                    publish=action == "freeze",
                    queue=payload.get("flow_queue"),
                )
            )
        except Exception as exc:  # noqa: BLE001 - serialize child failures for the parent.
            _emit({"error": f"{type(exc).__name__}: {exc}"})
        return 0

    if action == "lint":
        from composable_agents.ca.queues import queue_lane_diagnostics
        from composable_agents.validate import validate

        result = _discover_agent(root, src, target)
        if result.found is None:
            _emit({"error": _not_found_error(target, result.import_errors)})
            return 0
        diagnostics = validate(result.found.to_ir())
        extra = queue_lane_diagnostics(
            result.found,
            payload.get("queues") or {},
            str(payload.get("queue_env") or "local"),
        )
        _emit(
            {
                "diagnostics": [
                    {"code": d.code, "severity": d.severity, "message": d.message}
                    for d in diagnostics
                ]
                + extra
            }
        )
        return 0

    if action == "run":
        import asyncio

        from composable_agents.ca._echo import build_echo_env
        from composable_agents.execution.interpreter import interpret

        result = _discover_agent(root, src, target)
        if result.found is None:
            _emit({"error": _not_found_error(target, result.import_errors), "events": []})
            return 0
        node = result.found.to_ir()
        env, projection = build_echo_env(node)
        try:
            outcome = asyncio.run(interpret(node, payload.get("value"), env))
        except Exception as exc:  # noqa: BLE001 - serialize run failure for the parent.
            _emit(
                {
                    "value": None,
                    "events": [e.to_json() for e in projection.events()],
                    "error": str(exc),
                }
            )
            return 0
        _emit(
            {
                "value": outcome.value,
                "events": [e.to_json() for e in projection.events()],
                "error": None,
            }
        )
        return 0

    result = _discover_agent(root, src, target)
    found = result.found
    if found is None:
        _emit({"error": _not_found_error(target, result.import_errors)})
        return 0
    node = found.to_ir()
    _emit({"ir": node.to_json(), "name": target})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
