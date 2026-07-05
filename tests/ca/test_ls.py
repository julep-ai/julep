# tests/ca/test_ls.py
from julep.ca import cli


def test_ls_lists_all(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = cli.main(["ls"])
    out = capsys.readouterr().out
    assert code == 0
    assert "triage" in out and "escalate" in out and "support_bot" in out


def test_ls_with_selector(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = cli.main(["ls", "tag:support"])
    out = capsys.readouterr().out
    assert code == 0
    assert "triage" in out and "escalate" not in out
