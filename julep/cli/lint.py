from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from julep.cli.config import JulepConfig
from julep.cli.discover import scan_agents
from julep.cli.model import Agent, Module
from julep.cli.resolve import lint_agent
from julep.ctx_pipeline import pipeline_spec_from_ctx
from julep.dotctx import MissingOutputSchemaWarning, Reasoner
from julep.ir import Node
from julep.registry import Registry
from julep.validate import validate

_SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}


@dataclass(frozen=True)
class Finding:
    agent: str
    code: str
    severity: str
    message: str


def include_ctx_pipelines(cfg: JulepConfig, module: Module) -> Module:
    """Add configured zero-code pipelines to the lint selector namespace."""
    existing = {agent.name for agent in module.agents}
    configured = [
        Agent(
            name=name,
            kind="ctx",
            file=str((cfg.root / pipeline.ctx).resolve()),
            line=1,
            tags=list(cfg.tags.get(name, [])),
        )
        for name, pipeline in sorted(cfg.pipelines.items())
        if name not in existing
    ]
    return Module(root=module.root, agents=[*module.agents, *configured])


def _lint_ctx_pipeline(
    cfg: JulepConfig,
    name: str,
    *,
    env_vars: dict[str, str] | None,
    registry: Registry,
) -> tuple[list[Finding], str | None]:
    """Load and structurally validate one configured ctx pipeline, without IO.

    ``pipeline_spec_from_ctx`` validates tool bindings and only constructs the
    live MCP snapshot closure. It does not call the closure, compile/deploy an
    application, publish artifacts, or contact a configured server.
    """
    pipeline = cfg.pipelines[name]
    try:
        # The CLI renders the same condition as a structured finding below;
        # suppress the load-time Python warning to avoid duplicate output.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MissingOutputSchemaWarning)
            spec = pipeline_spec_from_ctx(
                pipeline,
                root=cfg.root,
                env_vars=env_vars,
                agent_round_cap=cfg.agent_round_cap,
                mcp_servers=cfg.mcp_servers,
                _registry=registry,
            )
    except Exception as exc:  # noqa: BLE001 - turn user package failures into diagnostics.
        return [], f"{type(exc).__name__}: {exc}"

    findings = [
        Finding(name, diagnostic.code, diagnostic.severity, diagnostic.message)
        for diagnostic in validate(cast(Node, spec.flow))
    ]
    reasoner = cast(Reasoner, spec.reasoners[0])
    if reasoner.reply_schema is None:
        ctx_path = Path(pipeline.ctx)
        if not ctx_path.is_absolute():
            ctx_path = cfg.root / ctx_path
        findings.append(
            Finding(
                name,
                "CTX_OUTPUT_SCHEMA_MISSING",
                "warning",
                (
                    f"dotctx package {str(ctx_path)!r} does not define class Output "
                    "in schema.pyi; model replies will not be schema-validated"
                ),
            )
        )
    return findings, None


def lint_agents(
    cfg: JulepConfig,
    names: list[str],
    *,
    fail_severity: str,
    env_vars: dict[str, str] | None = None,
    queues: dict[str, str] | None = None,
    queue_env: str = "local",
) -> tuple[list[Finding], int]:
    """Validate code agents and configured ctx pipelines, then gate by severity."""
    if fail_severity not in _SEVERITY_ORDER:
        raise ValueError(
            f"unknown fail_severity {fail_severity!r}; expected one of {sorted(_SEVERITY_ORDER)}"
        )
    floor = _SEVERITY_ORDER[fail_severity]
    findings: list[Finding] = []
    gated = False
    code_names = {agent.name for agent in scan_agents(cfg)}
    # Mirror application resolution without contaminating the process-global
    # registry. Sharing this scratch registry across selected pipelines keeps
    # cross-pipeline reasoner/renderer collision checks intact.
    registry = Registry()

    def append_finding(finding: Finding) -> None:
        nonlocal gated
        findings.append(finding)
        if _SEVERITY_ORDER.get(
            finding.severity,
            _SEVERITY_ORDER["error"],
        ) >= floor:
            gated = True

    for name in names:
        is_pipeline = name in cfg.pipelines
        if is_pipeline:
            pipeline_findings, error = _lint_ctx_pipeline(
                cfg,
                name,
                env_vars=env_vars,
                registry=registry,
            )
            if error is not None:
                return [Finding(name, "CTX_LOAD", "error", error)], 2
            for finding in pipeline_findings:
                append_finding(finding)

        # A configured pipeline can share a name with a discovered legacy
        # agent. Lint both rather than silently letting one shadow the other.
        if name in code_names or not is_pipeline:
            resolution = lint_agent(
                cfg,
                name,
                env_vars=env_vars,
                queues=queues,
                queue_env=queue_env,
            )
            if resolution.error is not None:
                return [Finding(name, "RESOLVE", "error", resolution.error)], 2
            for diagnostic in resolution.diagnostics:
                append_finding(
                    Finding(
                        name,
                        diagnostic["code"],
                        diagnostic["severity"],
                        diagnostic["message"],
                    )
                )

    return findings, 1 if gated else 0
