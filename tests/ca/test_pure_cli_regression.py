import subprocess
import sys
from pathlib import Path

import pytest

# A flow that uses a @pure. The pure body is echo-tolerant: it reads only
# dict.keys(), so it never KeyErrors under ca run's {"output": value} echo stubs.
PURE_SAMPLE = '''
from julep import flow, pure, think, tool

@tool(effect="read", idempotent=True)
def lookup(ticket: str) -> dict:
    return {"queue": "billing"}

@pure("passthrough")
def passthrough(hit: dict) -> dict:
    return {"seen": sorted(hit.keys())}

@flow
def triage(ticket: str) -> dict:
    hit = lookup(ticket)
    prompt = passthrough(hit)
    answer = think("reply", prompt)
    return prompt | answer
'''


@pytest.fixture
def pure_module(tmp_path: Path) -> Path:
    """A ca project whose only agent uses a @pure (the case the suite never covered)."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "agents.py").write_text(PURE_SAMPLE, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[tool.ca]\nsrc = ["pkg"]\n', encoding="utf-8")
    return tmp_path


def test_lint_resolves_pures_no_unknown_pure(pure_module: Path) -> None:
    from julep.ca.config import load_config
    from julep.ca.lint import lint_agents

    cfg = load_config(pure_module)
    findings, exit_code = lint_agents(cfg, ["triage"], fail_severity="error")
    codes = [f.code for f in findings]
    assert "UNKNOWN_PURE" not in codes, f"pure not resolved by ca lint: {findings}"
    assert "RESOLVE" not in codes, f"resolve failed: {findings}"
    assert exit_code == 0


def test_run_executes_pures_no_unknown_pure(pure_module: Path) -> None:
    from julep.ca.config import load_config
    from julep.ca.runner import run_agent_local

    cfg = load_config(pure_module)
    outcome = run_agent_local(cfg, "triage", "TICKET-42", run_id="t-pure")
    assert outcome.error is None, f"run failed: {outcome.error}"
    # The pure actually executed: its output ('seen') survives into the value.
    assert isinstance(outcome.value, dict) and "seen" in outcome.value


def test_run_large_input_not_limited_by_argv(pure_module: Path) -> None:
    # A large but valid --input must not blow the OS single-arg limit
    # (MAX_ARG_STRLEN, ~128 KiB on Linux). The child payload travels over stdin,
    # not argv. Regression for ca run serializing the input into one argv string
    # (Codex PR#9, P2 / WS1).
    from julep.ca.config import load_config
    from julep.ca.runner import run_agent_local

    cfg = load_config(pure_module)
    big = "X" * 300_000  # comfortably past MAX_ARG_STRLEN
    outcome = run_agent_local(cfg, "triage", big, run_id="t-big")
    assert outcome.error is None, f"run failed: {outcome.error}"
    assert isinstance(outcome.value, dict) and "seen" in outcome.value

def test_cli_lint_and_run_end_to_end(pure_module: Path) -> None:
    base = [sys.executable, "-m", "julep.ca.cli"]
    lint = subprocess.run(
        base + ["lint", "triage"], cwd=pure_module, capture_output=True, text=True
    )
    assert lint.returncode == 0, lint.stdout + lint.stderr
    assert "UNKNOWN_PURE" not in (lint.stdout + lint.stderr)

    run = subprocess.run(
        base + ["run", "triage", "--input", '"TICKET-42"'],
        cwd=pure_module,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "unknown pure" not in (run.stdout + run.stderr).lower()
    assert "output:" in run.stdout
