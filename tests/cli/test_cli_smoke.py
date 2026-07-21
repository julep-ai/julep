from importlib import import_module
import json

from julep import ident
from julep.cli.main import app, main


def test_version(capsys):
    code = main(["--version"])
    out = capsys.readouterr().out
    assert code == 0
    assert "julep" in out


def test_unknown_command_returns_2_no_traceback():
    # Click usage errors must be converted to a clean exit 2, not leaked.
    assert main(["doesnotexist"]) == 2


def test_no_args_returns_cleanly():
    # `julep` with no args triggers no-args-is-help; must not raise.
    code = main([])
    assert isinstance(code, int)


def test_commands_are_registered():
    # Guard against the package being reachable only via --version: the console
    # script must expose the full verb surface.
    names = {c.name for c in app.registered_commands}
    assert {
        "ls", "show", "graph", "run", "lint", "test", "trace", "doctor",
        "plan", "apply", "status", "worker", "artifact",
    } <= names


def test_artifact_help_delegates_to_artifact_cli(capsys):
    assert main(["artifact", "--help"]) == 0
    out = capsys.readouterr().out
    assert "usage: julep artifact" in out
    assert "validate" in out


def test_artifact_validate_delegates_with_exact_args(tmp_path, capsys):
    flow_path = tmp_path / "flow.json"
    flow_path.write_text(json.dumps(ident().to_json()), encoding="utf-8")

    assert main(["artifact", "validate", str(flow_path)]) == 0
    assert "No diagnostics" in capsys.readouterr().out


def test_worker_smoke_command_uses_environment_contract(monkeypatch):
    serve_module = import_module("julep.execution.serve")
    captured = []

    async def fake_smoke(settings, *, poll_seconds):
        captured.append((settings.context_factory, poll_seconds))

    monkeypatch.setenv("WORKER_CONTEXT_FACTORY", "memory.worker:context")
    monkeypatch.setattr(serve_module, "smoke_test_worker", fake_smoke)

    assert main(["worker", "--smoke-test-seconds", "0.25"]) == 0
    assert captured == [("memory.worker:context", 0.25)]


def test_worker_help_distinguishes_smoke_test_from_continuous_mode(capsys):
    assert main(["worker", "--help"]) == 0
    out = " ".join(capsys.readouterr().out.split())
    assert "Positive: verify Temporal" in out
    assert "Zero (default): run" in out
    assert "continuously." in out
