# tests/cli/test_run.py
from julep.cli.config import load_config
from julep.cli.runner import RunOutcome, run_agent_local


def test_run_triage_locally(sample_module):
    cfg = load_config(sample_module)
    outcome = run_agent_local(cfg, "triage", "TICKET-1", run_id="run-test-1")
    assert isinstance(outcome, RunOutcome)
    assert outcome.run_id == "run-test-1"
    assert outcome.events, "expected projection events"
    assert outcome.error is None


def test_run_unresolved_agent_surfaces_error(sample_module):
    cfg = load_config(sample_module)
    outcome = run_agent_local(cfg, "nope", "X", run_id="run-test-2")
    assert outcome.run_id == "run-test-2"
    assert outcome.error == "agent 'nope' not found"
    assert outcome.events == []
    assert outcome.value is None


def test_run_surfaces_runtime_error_without_crashing(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "agents.py").write_text(
        "from julep import flow, pure\n"
        "@pure('boom')\n"
        "def boom(x: str) -> dict:\n"
        "    raise RuntimeError('boom')\n"
        "@flow\n"
        "def explode(x: str) -> dict:\n"
        "    return boom(x)\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text('[tool.julep]\nsrc = ["pkg"]\n', encoding="utf-8")

    cfg = load_config(tmp_path)
    outcome = run_agent_local(cfg, "explode", "X", run_id="run-test-3")
    assert outcome.run_id == "run-test-3"
    assert outcome.error == "boom"
    assert outcome.value is None
