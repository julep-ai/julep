"""Queue-lane helpers for CA environments."""

from __future__ import annotations

from typing import Any


def resolve_queue_lane(name: str | None, lanes: dict[str, str], default: str) -> str:
    """Whole-pipeline lane resolution.

    None -> default; known lane -> mapped; unknown -> raw string.
    """
    if not name:
        return default
    return lanes.get(name, name)


def queue_lane_diagnostics(
    found: Any,
    queues: dict[str, str],
    env_name: str,
) -> list[dict[str, str]]:
    """Teach authors when a configured-lane environment sees an unknown lane name.

    Empty maps mean lanes are not in use. Unknown names remain valid raw queues at
    runtime, but during lint they are usually typos, so the diagnostic lists the
    configured lanes.
    """
    if not queues:
        return []

    from composable_agents.ir import SubStep

    candidates: set[str] = set()
    subflow_queues: object = getattr(found, "subflow_queues", lambda: {})()
    if isinstance(subflow_queues, dict):
        for name in subflow_queues.values():
            if isinstance(name, str) and name:
                candidates.add(name)

    def walk(node: Any) -> None:
        node_queues = getattr(node, "subflow_queues", None)
        if isinstance(node_queues, dict):
            for name in node_queues.values():
                if isinstance(name, str) and name:
                    candidates.add(name)
        step = getattr(node, "step", None)
        if isinstance(step, SubStep):
            queue = getattr(step.contract, "queue", None)
            if isinstance(queue, str) and queue:
                candidates.add(queue)
        for attr in ("left", "right", "body", "plan", "default"):
            child = getattr(node, attr, None)
            if child is not None:
                walk(child)
        cases = getattr(node, "cases", None)
        if isinstance(cases, dict):
            for child in cases.values():
                walk(child)

    to_ir = getattr(found, "to_ir", None)
    if callable(to_ir):
        walk(to_ir())

    return [
        {
            "code": "QUEUE_UNKNOWN_LANE",
            "severity": "error",
            "message": (
                f"subflow queue {name!r} is not a configured lane for env {env_name!r}; "
                f"configured lanes: {sorted(queues)}"
            ),
        }
        for name in sorted(candidates)
        if name not in queues
    ]
