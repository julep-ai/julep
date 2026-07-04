from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from julep.ca._resolve_child import _BEGIN, _END
from julep.ca.config import CaConfig


@dataclass(frozen=True)
class ResolvedAgent:
    name: str
    ir: dict[str, Any]
    error: str | None = None


def _extract_payload(stdout: str) -> dict[str, Any]:
    """Pull the JSON block written between the child's sentinel markers.

    Robust to arbitrary user ``print`` output before/after the payload — we look
    for the marked block rather than assuming JSON is the last stdout line.
    """
    start = stdout.rfind(_BEGIN)
    end = stdout.rfind(_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("resolver produced no payload")
    body = stdout[start + len(_BEGIN) : end].strip()
    data: dict[str, Any] = json.loads(body)
    return data


def _invoke_child(cfg: CaConfig, extra: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
    """Run the resolve child with ``{root, src, **extra}`` and return its payload dict.

    On any transport-level failure returns ``{"error": "<message>"}`` so callers
    have a single shape to branch on.
    """
    arg = json.dumps({"root": str(cfg.root), "src": cfg.src, **extra})
    try:
        # Payload travels over stdin, not argv: a large ``ca run`` input would
        # otherwise blow the OS single-argument limit (OSError [E2BIG]).
        proc = subprocess.run(
            [sys.executable, "-m", "julep.ca._resolve_child"],
            input=arg,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cfg.root),
        )
    except subprocess.TimeoutExpired:
        return {"error": f"resolution timed out after {timeout}s"}
    if proc.returncode != 0:
        return {"error": proc.stderr.strip() or "resolver failed"}
    try:
        return _extract_payload(proc.stdout)
    except (ValueError, json.JSONDecodeError) as exc:
        detail = proc.stderr.strip()
        return {"error": f"{exc}{f': {detail}' if detail else ''}"}


@dataclass(frozen=True)
class LintResolution:
    diagnostics: list[dict[str, str]]
    error: str | None = None


@dataclass(frozen=True)
class RunResolution:
    value: Any
    events: list[dict[str, Any]]
    error: str | None = None


def lint_agent(
    cfg: CaConfig,
    name: str,
    *,
    timeout: float = 30.0,
    env_vars: dict[str, str] | None = None,
    queues: dict[str, str] | None = None,
    queue_env: str = "local",
) -> LintResolution:
    """Validate an agent IN the child (where pures are registered) and return diagnostics."""
    data = _invoke_child(
        cfg,
        {
            "name": name,
            "action": "lint",
            "env_vars": env_vars,
            "queues": queues or {},
            "queue_env": queue_env,
        },
        timeout=timeout,
    )
    if "error" in data:
        return LintResolution(diagnostics=[], error=str(data["error"]))
    raw = data.get("diagnostics", [])
    return LintResolution(diagnostics=[dict(d) for d in raw], error=None)


def run_agent(
    cfg: CaConfig,
    name: str,
    value: Any,
    *,
    timeout: float = 30.0,
    env_vars: dict[str, str] | None = None,
) -> RunResolution:
    """Interpret an agent IN the child (echo env, pures live) and return value + events."""
    data = _invoke_child(
        cfg,
        {"name": name, "action": "run", "value": value, "env_vars": env_vars},
        timeout=timeout,
    )
    if "error" in data and "value" not in data:
        # transport-level failure (timeout / nonzero / parse) -> no events available
        return RunResolution(value=None, events=[], error=str(data["error"]))
    return RunResolution(
        value=data.get("value"),
        events=[dict(e) for e in data.get("events", [])],
        error=data.get("error"),
    )


def resolve_agent(
    cfg: CaConfig,
    name: str,
    *,
    timeout: float = 30.0,
    env_vars: dict[str, str] | None = None,
) -> ResolvedAgent:
    """Import the user's module in a subprocess and return the agent's serialized IR."""
    data = _invoke_child(cfg, {"name": name, "env_vars": env_vars}, timeout=timeout)
    if "error" in data:
        return ResolvedAgent(name=name, ir={}, error=str(data["error"]))
    return ResolvedAgent(name=str(data["name"]), ir=data["ir"], error=None)
