"""Persistent JSON cache for local ca runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from composable_agents.projection import ProjectionEvent


def _runs_dir(root: str) -> Path:
    return Path(root) / ".ca" / "runs"


def save_run(
    root: str,
    *,
    run_id: str,
    agent: str,
    status: str,
    events: list[ProjectionEvent],
) -> None:
    runs_dir = _runs_dir(root)
    runs_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "run_id": run_id,
        "agent": agent,
        "status": status,
        "events": [event.to_json() for event in events],
    }
    (runs_dir / f"{run_id}.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def load_run(root: str, run_id: str) -> dict[str, Any] | None:
    path = _runs_dir(root) / f"{run_id}.json"
    if not path.exists():
        return None

    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Run cache entry is not a JSON object: {path}")
    return data


def failed_agents(root: str) -> set[str]:
    runs_dir = _runs_dir(root)
    if not runs_dir.exists():
        return set()

    agents: set[str] = set()
    for path in runs_dir.glob("*.json"):
        data: Any = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("status") not in ("done", "ok"):
            agent = data.get("agent", "")
            if isinstance(agent, str):
                agents.add(agent)

    return agents - {""}
