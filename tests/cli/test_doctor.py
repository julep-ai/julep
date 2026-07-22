from __future__ import annotations

from julep.cli.config import load_config
from julep.cli.doctor import legacy_checks, run_checks
from julep.cli.main import main


def test_checks_report_discovery(sample_module):
    checks = run_checks(load_config(sample_module))
    names = {c.name for c in checks}
    assert "discovery" in names and "git" in names and "langfuse" in names
    discovery = next(c for c in checks if c.name == "discovery")
    assert discovery.ok  # sample module discovers 3 agents


def test_legacy_checks_report_config_state_and_environment(tmp_path):
    (tmp_path / "ca.toml").write_text("", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.ca]\n", encoding="utf-8")
    (tmp_path / ".ca").mkdir()

    checks = legacy_checks(
        tmp_path,
        environ={
            "CA_BATCH_RESULT_TIMEOUT_S": "30",
            "COMPOSABLE_WASM_FUEL": "100",
        },
    )
    details = "\n".join(check.detail for check in checks)

    assert "rename it to julep.toml" in details
    assert "rename it to [tool.julep]" in details
    assert "move retained state to .julep/" in details
    assert "JULEP_BATCH_RESULT_TIMEOUT_S" in details
    assert "JULEP_WASM_FUEL" in details


def test_legacy_checks_report_retired_artifact_store_environment(tmp_path):
    checks = legacy_checks(
        tmp_path,
        environ={"JULEP_CAS_URL": "file:///old", "STORE_URL": "s3://old"},
    )

    details = "\n".join(check.detail for check in checks)
    assert "JULEP_CAS_URL is set; rename it to JULEP_ARTIFACT_STORE_URL" in details
    assert "STORE_URL is set; rename it to JULEP_ARTIFACT_STORE_URL" in details


def test_doctor_reports_legacy_config_without_parsing_it(tmp_path, monkeypatch, capsys):
    (tmp_path / "ca.toml").write_text("not valid TOML = [", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["doctor"]) == 0
    assert "ca.toml found; rename it to julep.toml" in capsys.readouterr().out
