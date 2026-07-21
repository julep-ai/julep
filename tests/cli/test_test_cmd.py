# tests/cli/test_test_cmd.py
from julep.cli.main import main


def test_test_runs_pytest_for_selection(sample_module, capsys, monkeypatch):
    # Provide a trivial passing test in the module so pytest exits 0.
    (sample_module / "test_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    monkeypatch.chdir(sample_module)
    code = main(["test", "triage", "--dry-run"])
    out = capsys.readouterr().out
    assert code == 0
    assert "pytest" in out  # --dry-run prints the command it would run
    assert "-k" in out and "triage" in out


def test_test_no_match_selector_does_not_run_whole_suite(sample_module, capsys, monkeypatch):
    monkeypatch.chdir(sample_module)
    code = main(["test", "zzznomatch", "--dry-run"])
    out = capsys.readouterr().out
    assert code == 0
    assert "no agents matched" in out
    assert "pytest" not in out  # must NOT fall through to a full-suite run
