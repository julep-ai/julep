# tests/ca/test_test_cmd.py
from composable_agents.ca import cli


def test_test_runs_pytest_for_selection(sample_module, capsys, monkeypatch):
    # Provide a trivial passing test in the module so pytest exits 0.
    (sample_module / "test_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    monkeypatch.chdir(sample_module)
    code = cli.main(["test", "triage", "--dry-run"])
    out = capsys.readouterr().out
    assert code == 0
    assert "pytest" in out  # --dry-run prints the command it would run
    assert "-k" in out and "triage" in out
