from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from julep.cli.config import JulepConfig
from julep.cli.resolve import RunResolution, run_agent
from julep.projection import ProjectionEvent


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    value: Any
    events: list[ProjectionEvent] = field(default_factory=list)
    error: str | None = None


def run_agent_local(
    cfg: JulepConfig,
    name: str,
    value: Any,
    *,
    run_id: str,
    env_vars: dict[str, str] | None = None,
) -> RunOutcome:
    """Execute an agent locally by interpreting it in the resolve child (pures live)."""
    resolution: RunResolution = run_agent(cfg, name, value, env_vars=env_vars)
    events = [ProjectionEvent.from_json(e) for e in resolution.events]
    return RunOutcome(run_id=run_id, value=resolution.value, events=events, error=resolution.error)
