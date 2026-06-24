# tests/ca/test_trace.py
import json

from composable_agents.ca import cli


def test_trace_renders_cached_run(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    cli.main(["run", "triage", "--input", json.dumps("TICKET-7"), "--run-id", "r-trace-1"])
    capsys.readouterr()  # clear
    code = cli.main(["trace", "r-trace-1"])
    out = capsys.readouterr().out
    assert code == 0
    assert "triage" in out or "[ok]" in out


def test_trace_prints_link_when_configured(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    cli.main(["run", "triage", "--input", json.dumps("T"), "--run-id", "r-trace-2"])
    capsys.readouterr()
    cli.main(["trace", "r-trace-2"])
    out = capsys.readouterr().out
    assert "cloud.langfuse.com" in out


def test_trace_unknown_run_returns_2(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    assert cli.main(["trace", "ghost"]) == 2
