from __future__ import annotations

from pathlib import Path

from composable_agents.ca import cli

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


def test_deploy_writes_ledger(sample_module: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(sample_module)

    code = cli.main(["deploy", "triage", "--env", "local"])
    out = capsys.readouterr().out

    assert code == 0
    assert (sample_module / ".ca" / "deploys" / "local.json").is_file()
    assert "triage" in out


def test_status_clean_after_deploy(sample_module: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(sample_module)

    assert cli.main(["deploy", "triage", "--env", "local"]) == 0
    capsys.readouterr()
    code = cli.main(["status", "--env", "local", "triage"])
    out = capsys.readouterr().out

    assert code == 0
    assert "clean" in out


def test_status_drift_exit_3(sample_module: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(sample_module)

    assert cli.main(["deploy", "triage", "--env", "local"]) == 0
    capsys.readouterr()
    (sample_module / "pkg" / "agents.py").write_text(_MUTATED_AGENTS, encoding="utf-8")
    code = cli.main(["status", "--env", "local", "triage"])
    out = capsys.readouterr().out

    assert code == 3
    assert "drift" in out


def test_run_local_unchanged(sample_module: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(sample_module)

    code = cli.main(["run", "triage", "--input", '"TICKET-9"', "--run-id", "rc1"])
    out = capsys.readouterr().out

    assert code == 0
    assert "triage" in out or "[ok]" in out
    assert (sample_module / ".ca" / "runs" / "rc1.json").is_file()
