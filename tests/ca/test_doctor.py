from __future__ import annotations

from julep.ca.config import load_config
from julep.ca.doctor import run_checks


def test_checks_report_discovery(sample_module):
    checks = run_checks(load_config(sample_module))
    names = {c.name for c in checks}
    assert "discovery" in names and "git" in names and "langfuse" in names
    discovery = next(c for c in checks if c.name == "discovery")
    assert discovery.ok  # sample module discovers 3 agents
