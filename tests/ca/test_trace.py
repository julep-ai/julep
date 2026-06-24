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


def test_trace_unknown_run_returns_2_even_with_langfuse(sample_module, capsys, monkeypatch):
    # A configured Langfuse host must not mask a missing local run via a
    # fabricated (hashed) deep link.
    monkeypatch.chdir(sample_module)
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    code = cli.main(["trace", "ghost-run-xyz"])
    captured = capsys.readouterr()
    assert code == 2
    assert "no cached run" in captured.err
    assert "langfuse" not in captured.out


def test_trace_error_run_surfaces_status(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    from composable_agents.ca.runcache import save_run

    save_run(str(sample_module), run_id="r-err", agent="triage", status="error", events=[])
    code = cli.main(["trace", "r-err"])
    out = capsys.readouterr().out
    assert code == 0
    assert "status=error" in out
