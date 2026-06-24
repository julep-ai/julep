"""Status and drift helpers for ca deployments.

Exit code 0 means no drift was found; exit code 3 means drift or freeze errors
were found.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from composable_agents.ca.config import CaConfig
from composable_agents.ca.deploy import freeze_agent
from composable_agents.ca.ledger import read_ledger
from composable_agents.ca.model import build_module


@dataclass(frozen=True)
class AgentStatus:
    name: str
    state: str
    deployed_hash: str | None
    current_hash: str | None
    detail: str = ""


def status_for_env(cfg: CaConfig, env: str) -> list[AgentStatus]:
    agents = build_module(cfg).agents
    source_names = {agent.name for agent in agents}
    ledger = read_ledger(cfg.root, env)
    ledger_names = set(ledger)

    statuses: list[AgentStatus] = []
    for name in sorted(source_names | ledger_names):
        record = ledger.get(name)
        if record is None:
            statuses.append(
                AgentStatus(
                    name=name,
                    state="undeployed",
                    deployed_hash=None,
                    current_hash=None,
                )
            )
            continue

        if name not in source_names:
            statuses.append(
                AgentStatus(
                    name=name,
                    state="drift",
                    deployed_hash=record.artifact_hash,
                    current_hash=None,
                    detail="deployed agent missing from source",
                )
            )
            continue

        # Status is read-only: compute the artifact hash WITHOUT publishing to
        # CAS / uploading to S3 (publish=False).
        artifact = freeze_agent(cfg, name, env, publish=False)
        if artifact.error is not None:
            statuses.append(
                AgentStatus(
                    name=name,
                    state="error",
                    deployed_hash=record.artifact_hash,
                    current_hash=None,
                    detail=artifact.error,
                )
            )
        elif artifact.artifact_hash == record.artifact_hash:
            statuses.append(
                AgentStatus(
                    name=name,
                    state="clean",
                    deployed_hash=record.artifact_hash,
                    current_hash=artifact.artifact_hash,
                )
            )
        else:
            statuses.append(
                AgentStatus(
                    name=name,
                    state="drift",
                    deployed_hash=record.artifact_hash,
                    current_hash=artifact.artifact_hash,
                )
            )

    return statuses


def status_exit_code(statuses: Iterable[AgentStatus]) -> int:
    if any(status.state in {"drift", "error"} for status in statuses):
        return 3
    return 0
