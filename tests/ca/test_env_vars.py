# tests/ca/test_env_vars.py
"""`[env.<name>.vars]` -> dotctx yglu default env, bound inside the resolver child.

The binding must reach the process that imports user modules: `ca run`/`lint`/
`deploy` resolve and freeze in a subprocess, so a user module calling
``load_dotctx`` at import time must see the env profile there — not in the CLI
parent.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from composable_agents.ca.config import load_config


def test_env_vars_parsed(tmp_path: Path) -> None:
    (tmp_path / "ca.toml").write_text(
        '[env.prod]\n'
        'task_queue = "prod-q"\n'
        '[env.prod.vars]\n'
        'SUMMARY_MODEL = "anthropic:claude-sonnet-4-6@high"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.envs["prod"].vars == {
        "SUMMARY_MODEL": "anthropic:claude-sonnet-4-6@high"}
    # scalar fields on the same table are unaffected
    assert cfg.envs["prod"].task_queue == "prod-q"


def test_env_vars_default_empty(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert cfg.envs["local"].vars == {}


def test_env_vars_merge_ca_toml_over_pyproject(tmp_path: Path) -> None:
    """Per-key merge, ca.toml over pyproject — same precedence as scalar fields."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.ca.env.prod.vars]\n"
        'SUMMARY_MODEL = "from-pyproject"\n'
        'KEEP = "kept"\n',
        encoding="utf-8",
    )
    (tmp_path / "ca.toml").write_text(
        "[env.prod.vars]\n"
        'SUMMARY_MODEL = "from-ca-toml"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.envs["prod"].vars == {
        "SUMMARY_MODEL": "from-ca-toml", "KEEP": "kept"}


# --------------------------------------------------------------------------- #
# End-to-end: the binding is visible at user-module import time IN THE CHILD.
# --------------------------------------------------------------------------- #

_SETTINGS = 'model: !? $env.get("SUMMARY_MODEL", "openai:gpt-4o")\n'

# The module asserts at import time, inside the resolver child: if the ca env
# profile is not bound there, the yglu default wins and the import fails.
_MODULE = (
    "import os\n"
    "from composable_agents import flow, think\n"
    "from composable_agents.dotctx import load_dotctx\n"
    "R = load_dotctx(os.path.join(os.path.dirname(__file__), 'summary.ctx'))\n"
    "assert R.model == 'anthropic:claude-sonnet-4-6', f'model={R.model}'\n"
    "assert R.reasoning_effort == 'high', f'effort={R.reasoning_effort}'\n"
    "@flow\n"
    "def summary(x: str) -> dict:\n"
    "    return think(R, x)\n"
)


def _project(tmp_path: Path) -> Path:
    ctx = tmp_path / "flows" / "summary.ctx"
    ctx.mkdir(parents=True)
    (ctx / "settings.yaml").write_text(_SETTINGS, encoding="utf-8")
    (tmp_path / "flows" / "mod.py").write_text(_MODULE, encoding="utf-8")
    (tmp_path / "ca.toml").write_text(
        'src = ["flows"]\n'
        "[env.prod.vars]\n"
        'SUMMARY_MODEL = "anthropic:claude-sonnet-4-6@high"\n',
        encoding="utf-8",
    )
    return tmp_path


def test_run_binds_env_vars_in_resolver_child(tmp_path: Path) -> None:
    pytest.importorskip("yglu")
    from composable_agents.ca.runner import run_agent_local

    cfg = load_config(_project(tmp_path))
    outcome = run_agent_local(
        cfg, "summary", "hello", run_id="run-env-1",
        env_vars=cfg.envs["prod"].vars,
    )
    assert outcome.error is None, outcome.error
    assert outcome.run_id == "run-env-1"


def test_resolver_child_without_env_vars_sees_defaults(tmp_path: Path) -> None:
    pytest.importorskip("yglu")
    from composable_agents.ca.resolve import resolve_agent

    cfg = load_config(_project(tmp_path))
    resolved = resolve_agent(cfg, "summary")
    assert resolved.error is not None
    # No binding -> $env.get yields the yglu default -> the module's assert fires.
    assert "model=openai:gpt-4o" in resolved.error


def test_freeze_payload_carries_env_vars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ca deploy --env prod` freezes in a child; the payload must carry the vars."""
    from composable_agents.ca import deploy as deploy_mod
    from composable_agents.ca._resolve_child import _BEGIN, _END

    captured: dict[str, Any] = {}

    class _Proc:
        returncode = 0
        stdout = f"{_BEGIN}\n{json.dumps({'error': 'stop'})}\n{_END}\n"
        stderr = ""

    def fake_run(*args: Any, **kwargs: Any) -> _Proc:
        captured.update(json.loads(kwargs["input"]))
        return _Proc()

    monkeypatch.setattr(deploy_mod.subprocess, "run", fake_run)
    (tmp_path / "ca.toml").write_text(
        "[env.prod.vars]\n"
        'SUMMARY_MODEL = "anthropic:claude-sonnet-4-6@high"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    deploy_mod.freeze_agent(cfg, "summary", "prod")
    assert captured["action"] == "freeze"
    assert captured["env_vars"] == {
        "SUMMARY_MODEL": "anthropic:claude-sonnet-4-6@high"}
