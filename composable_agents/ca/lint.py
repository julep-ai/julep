from __future__ import annotations

from dataclasses import dataclass

from composable_agents.ca.config import CaConfig
from composable_agents.ca.resolve import lint_agent

_SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}


@dataclass(frozen=True)
class Finding:
    agent: str
    code: str
    severity: str
    message: str


def lint_agents(
    cfg: CaConfig,
    names: list[str],
    *,
    fail_severity: str,
    env_vars: dict[str, str] | None = None,
) -> tuple[list[Finding], int]:
    """Validate agents (in-child, where pures are live) and gate by severity."""
    if fail_severity not in _SEVERITY_ORDER:
        raise ValueError(
            f"unknown fail_severity {fail_severity!r}; expected one of {sorted(_SEVERITY_ORDER)}"
        )
    floor = _SEVERITY_ORDER[fail_severity]
    findings: list[Finding] = []
    gated = False

    for name in names:
        resolution = lint_agent(cfg, name, env_vars=env_vars)
        if resolution.error is not None:
            return [Finding(name, "RESOLVE", "error", resolution.error)], 2
        for d in resolution.diagnostics:
            severity = d["severity"]
            findings.append(Finding(name, d["code"], severity, d["message"]))
            if _SEVERITY_ORDER.get(severity, _SEVERITY_ORDER["error"]) >= floor:
                gated = True

    return findings, 1 if gated else 0
