from __future__ import annotations

from pathlib import Path

from composable_agents.ca.config import load_config
from composable_agents.ca.deploy import deploy_agents
from composable_agents.ca.status import AgentStatus, status_exit_code, status_for_env

_NOW = "2026-06-23T00:00:00Z"

_MUTATED_AGENTS = '''
from composable_agents import flow, think, tool, Agent

@tool(effect="read", idempotent=True)
def lookup(ticket: str) -> dict:
    return {"hit": ticket}

@flow
def triage(ticket: str) -> dict:
    hit = lookup(ticket)
    answer = think("reply-changed", hit)
    return hit | answer

@flow
def escalate(case: dict) -> dict:
    routed = triage(case)          # cross-agent call -> edge triage->escalate
    return routed

support_bot = Agent("reply", tools=[lookup], name="support_bot")
'''


def _by_name(statuses: list[AgentStatus]) -> dict[str, AgentStatus]:
    return {status.name: status for status in statuses}


def test_status_undeployed(sample_module: Path) -> None:
    cfg = load_config(sample_module)

    statuses = _by_name(status_for_env(cfg, "local"))

    assert statuses["triage"].state == "undeployed"
    assert statuses["triage"].deployed_hash is None
    assert statuses["escalate"].state == "undeployed"
    assert statuses["escalate"].deployed_hash is None
    assert status_exit_code(statuses.values()) == 0


def test_status_clean_after_deploy(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    deploy_agents(cfg, ["triage"], "local", now_iso=_NOW)

    status = _by_name(status_for_env(cfg, "local"))["triage"]

    assert status.state == "clean"
    assert status.deployed_hash == status.current_hash
    assert status.deployed_hash is not None
    assert status.deployed_hash.startswith("sha256:")
    assert status_exit_code([status]) == 0


def test_status_drift_after_source_mutation(sample_module: Path) -> None:
    cfg = load_config(sample_module)
    deploy_agents(cfg, ["triage"], "local", now_iso=_NOW)
    (sample_module / "pkg" / "agents.py").write_text(_MUTATED_AGENTS, encoding="utf-8")
    cfg = load_config(sample_module)

    status = _by_name(status_for_env(cfg, "local"))["triage"]

    assert status.state == "drift"
    assert status.deployed_hash is not None
    assert status.current_hash is not None
    assert status.deployed_hash.startswith("sha256:")
    assert status.current_hash.startswith("sha256:")
    assert status.deployed_hash != status.current_hash
    assert status_exit_code([status]) == 3


def test_status_exit_code_helper() -> None:
    clean = AgentStatus("clean", "clean", "sha256:1", "sha256:1")
    undeployed = AgentStatus("undeployed", "undeployed", None, None)
    drift = AgentStatus("drift", "drift", "sha256:1", "sha256:2")
    error = AgentStatus("error", "error", "sha256:1", None, "freeze failed")

    assert status_exit_code([clean]) == 0
    assert status_exit_code([clean, undeployed]) == 0
    assert status_exit_code([drift]) == 3
    assert status_exit_code([error]) == 3
