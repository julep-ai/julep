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


def test_deploy_unknown_env_exits_2_no_traceback(sample_module: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(sample_module)

    code = cli.main(["deploy", "triage", "--env", "staging"])
    err = capsys.readouterr().err

    assert code == 2
    assert "unknown env" in err
    assert "staging" in err
    # The bad env must not have written a ledger.
    assert not (sample_module / ".ca" / "deploys" / "staging.json").exists()


def test_status_unknown_env_exits_2_no_traceback(sample_module: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(sample_module)

    code = cli.main(["status", "--env", "staging"])
    err = capsys.readouterr().err

    assert code == 2
    assert "unknown env" in err


def test_status_does_not_publish_to_cas(sample_module: Path, capsys, monkeypatch) -> None:
    """`ca status` is read-only: it must not write CAS objects on a clean check."""
    monkeypatch.chdir(sample_module)

    assert cli.main(["deploy", "triage", "--env", "local"]) == 0
    capsys.readouterr()

    cas_root = sample_module / ".ca" / "cas"
    import shutil

    shutil.rmtree(cas_root, ignore_errors=True)

    code = cli.main(["status", "--env", "local", "triage"])
    out = capsys.readouterr().out

    assert code == 0
    assert "clean" in out
    # Status compared hashes without re-publishing -> no CAS dir recreated.
    assert not cas_root.exists()
