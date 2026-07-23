"""Persistent JSON cache for local Julep runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from julep.projection import ProjectionEvent


def _runs_dir(root: str) -> Path:
    return Path(root) / ".julep" / "runs"


def _event_for_cache(event: ProjectionEvent) -> dict[str, Any]:
    """Project an event to the non-sensitive fields needed by ``julep trace``.

    Projection attributes can include model inputs/outputs, and failure text can
    include provider payloads. The local run cache is clear-text by design, so
    neither belongs on disk. Preserve only structural trace data plus the
    boolean cost-unknown signal used by the tree renderer.
    """
    cached: dict[str, Any] = {
        "eventId": event.event_id,
        "type": event.type.value,
        "node": event.node,
        "cid": event.cid,
        "ts": event.ts,
        "causes": list(event.causes),
    }
    for key, value in (
        ("valueRef", event.value_ref),
        ("shape", event.shape),
        ("cost", event.cost),
    ):
        if value is not None:
            cached[key] = value
    if (
        event.attrs.get("llm.cost.status") == "unknown"
        or "llm.model" in event.attrs
        or "llm.usage" in event.attrs
    ):
        cached["attrs"] = {"llm.cost.status": "unknown"}
    return cached


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
        "events": [_event_for_cache(event) for event in events],
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
