from composable_agents.ca import cli


def test_version(capsys):
    code = cli.main(["--version"])
    out = capsys.readouterr().out
    assert code == 0
    assert "ca" in out
