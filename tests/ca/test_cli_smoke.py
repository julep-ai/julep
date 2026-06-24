from composable_agents.ca import cli


def test_version(capsys):
    code = cli.main(["--version"])
    out = capsys.readouterr().out
    assert code == 0
    assert "ca" in out


def test_commands_are_registered():
    # Guard against the package being reachable only via --version: the console
    # script must expose the full verb surface.
    names = {c.name for c in cli.app.registered_commands}
    assert {"ls", "show", "graph", "run", "lint", "test", "trace", "doctor"} <= names
