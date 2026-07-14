from importlib import import_module

from julep.ca import cli


def test_version(capsys):
    code = cli.main(["--version"])
    out = capsys.readouterr().out
    assert code == 0
    assert "julep" in out


def test_unknown_command_returns_2_no_traceback():
    # Click usage errors must be converted to a clean exit 2, not leaked.
    assert cli.main(["doesnotexist"]) == 2


def test_no_args_returns_cleanly():
    # `julep` with no args triggers no-args-is-help; must not raise.
    code = cli.main([])
    assert isinstance(code, int)


def test_commands_are_registered():
    # Guard against the package being reachable only via --version: the console
    # script must expose the full verb surface.
    names = {c.name for c in cli.app.registered_commands}
    assert {
        "ls", "show", "graph", "run", "lint", "test", "trace", "doctor",
        "plan", "apply", "status", "worker",
    } <= names


def test_worker_smoke_command_uses_environment_contract(monkeypatch):
    serve_module = import_module("julep.execution.serve")
    captured = []

    async def fake_smoke(settings, *, poll_seconds):
        captured.append((settings.context_factory, poll_seconds))

    monkeypatch.setenv("WORKER_CONTEXT_FACTORY", "memory.worker:context")
    monkeypatch.setattr(serve_module, "smoke_test_worker", fake_smoke)

    assert cli.main(["worker", "--smoke-test-seconds", "0.25"]) == 0
    assert captured == [("memory.worker:context", 0.25)]


def test_worker_help_distinguishes_smoke_test_from_continuous_mode(capsys):
    assert cli.main(["worker", "--help"]) == 0
    out = " ".join(capsys.readouterr().out.split())
    assert "Positive: verify Temporal" in out
    assert "Zero (default): run" in out
    assert "continuously." in out
