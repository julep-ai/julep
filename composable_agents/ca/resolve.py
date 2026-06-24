from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from composable_agents.ca._resolve_child import _BEGIN, _END
from composable_agents.ca.config import CaConfig


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


def resolve_agent(cfg: CaConfig, name: str, *, timeout: float = 30.0) -> ResolvedAgent:
    """Import the user's module in a subprocess and return the agent's serialized IR."""
    arg = json.dumps({"root": str(cfg.root), "src": cfg.src, "name": name})
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "composable_agents.ca._resolve_child", arg],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cfg.root),
        )
    except subprocess.TimeoutExpired:
        return ResolvedAgent(name=name, ir={}, error=f"resolution timed out after {timeout}s")
    if proc.returncode != 0:
        return ResolvedAgent(name=name, ir={}, error=proc.stderr.strip() or "resolver failed")
    try:
        data = _extract_payload(proc.stdout)
    except (ValueError, json.JSONDecodeError) as exc:
        detail = proc.stderr.strip()
        return ResolvedAgent(name=name, ir={}, error=f"{exc}{f': {detail}' if detail else ''}")
    if "error" in data:
        return ResolvedAgent(name=name, ir={}, error=str(data["error"]))
    return ResolvedAgent(name=str(data["name"]), ir=data["ir"], error=None)
