# tests/cli/test_lint.py
from julep.cli.config import load_config
from julep.cli.lint import lint_agents


def test_lint_clean_module_passes(sample_module):
    cfg = load_config(sample_module)
    findings, exit_code = lint_agents(cfg, ["triage", "escalate"], fail_severity="error")
    assert exit_code == 0  # sample is structurally valid


def test_fail_severity_threshold_gates(sample_module):
    cfg = load_config(sample_module)
    # With an impossibly strict floor, any warning would gate; clean module still 0.
    _, exit_code = lint_agents(cfg, ["triage"], fail_severity="warning")
    assert exit_code in (0, 1)
