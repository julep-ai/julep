# tests/cli/test_trace.py
import json
from urllib.parse import urlparse

from julep.cli.main import main


def test_trace_renders_cached_run(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    main(["run", "triage", "--input", json.dumps("TICKET-7"), "--run-id", "r-trace-1"])
    capsys.readouterr()  # clear
    code = main(["trace", "r-trace-1"])
    out = capsys.readouterr().out
    assert code == 0
    assert "triage" in out or "[ok]" in out


def test_trace_prints_link_when_configured(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    main(["run", "triage", "--input", json.dumps("T"), "--run-id", "r-trace-2"])
    capsys.readouterr()
    main(["trace", "r-trace-2"])
    out = capsys.readouterr().out
    link = out.strip().splitlines()[-1].removeprefix("langfuse: ")
    parsed = urlparse(link)
    assert parsed.scheme == "https"
    assert parsed.hostname == "cloud.langfuse.com"


def test_trace_unknown_run_returns_2(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    assert main(["trace", "ghost"]) == 2


def test_trace_unknown_run_returns_2_even_with_langfuse(sample_module, capsys, monkeypatch):
    # A configured Langfuse host must not mask a missing local run via a
    # fabricated (hashed) deep link.
    monkeypatch.chdir(sample_module)
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    code = main(["trace", "ghost-run-xyz"])
    captured = capsys.readouterr()
    assert code == 2
    assert "no cached run" in captured.err
    assert "langfuse" not in captured.out


def test_trace_error_run_surfaces_status(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    from julep.cli.runcache import save_run

    save_run(str(sample_module), run_id="r-err", agent="triage", status="error", events=[])
    code = main(["trace", "r-err"])
    out = capsys.readouterr().out
    assert code == 0
    assert "status=error" in out
