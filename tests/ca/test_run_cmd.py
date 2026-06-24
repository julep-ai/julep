# tests/ca/test_run_cmd.py
import json

from composable_agents.ca import cli


def test_run_prints_tree_and_caches(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = cli.main(["run", "triage", "--input", json.dumps("TICKET-9"), "--run-id", "r-cmd-1"])
    out = capsys.readouterr().out
    assert code == 0
    assert "triage" in out or "[ok]" in out
    assert (sample_module / ".ca" / "runs" / "r-cmd-1.json").is_file()
