from julep.ca import cli


def test_version(capsys):
    code = cli.main(["--version"])
    out = capsys.readouterr().out
    assert code == 0
    assert "ca" in out


def test_unknown_command_returns_2_no_traceback():
    # Click usage errors must be converted to a clean exit 2, not leaked.
    assert cli.main(["doesnotexist"]) == 2


def test_no_args_returns_cleanly():
    # `ca` with no args triggers no-args-is-help; must not raise.
    code = cli.main([])
    assert isinstance(code, int)


def test_commands_are_registered():
    # Guard against the package being reachable only via --version: the console
    # script must expose the full verb surface.
    names = {c.name for c in cli.app.registered_commands}
    assert {"ls", "show", "graph", "run", "lint", "test", "trace", "doctor"} <= names
