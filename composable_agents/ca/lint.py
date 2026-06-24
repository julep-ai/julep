from __future__ import annotations

from dataclasses import dataclass

from composable_agents.ca.config import CaConfig
from composable_agents.ca.resolve import resolve_agent
from composable_agents.ir import Node
from composable_agents.validate import Diagnostic, validate

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
) -> tuple[list[Finding], int]:
    """Resolve agents to IR, validate them, and return findings plus an exit code."""
    findings: list[Finding] = []
    floor = _SEVERITY_ORDER.get(fail_severity, _SEVERITY_ORDER["error"])
    gated = False

    for name in names:
        resolved = resolve_agent(cfg, name)
        if resolved.error is not None:
            return [Finding(name, "RESOLVE", "error", resolved.error)], 2

        diagnostics: list[Diagnostic] = validate(Node.from_json(resolved.ir))
        for diagnostic in diagnostics:
            findings.append(
                Finding(
                    name,
                    diagnostic.code,
                    diagnostic.severity,
                    diagnostic.message,
                )
            )
            if _SEVERITY_ORDER.get(diagnostic.severity, _SEVERITY_ORDER["error"]) >= floor:
                gated = True

    return findings, 1 if gated else 0
