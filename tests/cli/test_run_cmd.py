# tests/cli/test_run_cmd.py
import json

from julep.cli.main import main


def test_run_prints_tree_and_caches(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = main(["run", "triage", "--input", json.dumps("TICKET-9"), "--run-id", "r-cmd-1"])
    out = capsys.readouterr().out
    assert code == 0
    assert "triage" in out or "[ok]" in out
    assert (sample_module / ".julep" / "runs" / "r-cmd-1.json").is_file()


def test_run_invalid_input_json_returns_2(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = main(["run", "triage", "--input", "not json", "--run-id", "r-bad"])
    err = capsys.readouterr().err
    assert code == 2
    assert "invalid --input JSON" in err
