# tests/ca/conftest.py
from pathlib import Path

import pytest

SAMPLE = '''
from julep import flow, think, tool, Agent

@tool(effect="read", idempotent=True)
def lookup(ticket: str) -> dict:
    return {"hit": ticket}

@flow
def triage(ticket: str) -> dict:
    hit = lookup(ticket)
    answer = think("reply", hit)
    return hit | answer

@flow
def escalate(case: dict) -> dict:
    routed = triage(case)          # cross-agent call -> edge triage->escalate
    return routed

support_bot = Agent("reply", tools=[lookup], name="support_bot")
'''


@pytest.fixture
def sample_module(tmp_path: Path) -> Path:
    """A repo root with one package `pkg` holding two @flow agents and one Agent instance."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "agents.py").write_text(SAMPLE, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ca]\nsrc = ["pkg"]\n[tool.ca.tags]\ntriage = ["support"]\n',
        encoding="utf-8",
    )
    return tmp_path
