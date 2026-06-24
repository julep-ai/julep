from __future__ import annotations

import importlib.util
import os
import shutil
from dataclasses import dataclass

from composable_agents.ca.config import CaConfig
from composable_agents.ca.model import build_module


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def run_checks(cfg: CaConfig) -> list[Check]:
    checks: list[Check] = []
    module = build_module(cfg)
    n = len(module.agents)
    where = ", ".join(cfg.src) if cfg.src else str(cfg.root)
    checks.append(Check("discovery", n > 0, f"{n} agent(s) discovered under {where}"))

    has_git = shutil.which("git") is not None
    checks.append(Check("git", has_git, "git found" if has_git else "git not on PATH (state:modified disabled)"))

    lf = bool(os.environ.get("LANGFUSE_HOST"))
    checks.append(Check("langfuse", lf, "LANGFUSE_HOST set" if lf else "LANGFUSE_HOST unset (no deep links)"))

    has_temporal = importlib.util.find_spec("temporalio") is not None
    checks.append(Check("temporal", has_temporal, "temporalio installed" if has_temporal else "temporalio missing (deploy disabled)"))

    return checks


def overall_code(checks: list[Check]) -> int:
    """Exit 1 only if a hard-required check (discovery) fails; soft checks are warnings."""
    discovery = next((c for c in checks if c.name == "discovery"), None)
    return 0 if (discovery is None or discovery.ok) else 1
