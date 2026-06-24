# tests/ca/test_show.py
from composable_agents.ca import cli


def test_show_one_agent(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = cli.main(["show", "escalate"])
    out = capsys.readouterr().out
    assert code == 0
    assert "escalate" in out
    assert "triage" in out  # lists the cross-agent call
    assert "agents.py" in out  # source location


def test_show_unknown_returns_error(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = cli.main(["show", "nope"])
    assert code == 2
