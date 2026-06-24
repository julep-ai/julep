from composable_agents.ca import cli


def test_trigger_sends_one_event(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)

    code = cli.main(["trigger", "triage", '"TICKET-9"'])
    captured = capsys.readouterr()

    assert code == 0
    assert "<- " in captured.out
    assert "TICKET-9" in captured.out


def test_trigger_unknown_agent_exit_2(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)

    code = cli.main(["trigger", "nope", '"TICKET-9"'])
    captured = capsys.readouterr()

    assert code == 2
    assert "error:" in captured.err
    assert "not found" in captured.err


def test_trigger_rejects_unsupported_channel(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)

    code = cli.main(["trigger", "triage", '"TICKET-9"', "--channel", "out"])
    captured = capsys.readouterr()

    assert code == 2
    assert "unsupported channel" in captured.err
    assert "out" in captured.err


def test_trigger_help_present(capsys):
    code = cli.main(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    assert "trigger" in out

    code = cli.main(["trigger", "--help"])
    assert code == 0
