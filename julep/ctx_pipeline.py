"""Configuration-backed dotctx application pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from .app import PipelineSpec
from .dotctx import load_dotctx, reasoner_to_flow
from .execution.policy import ExecutionPolicy
from .freeze import McpSnapshot


@dataclass(frozen=True)
class CtxPipelineConfig:
    name: str
    ctx: str
    lane: str = "default"
    env: dict[str, str] = field(default_factory=dict)
    # Prompt-visible bare alias -> configured MCP wire target (server:tool).
    tools: dict[str, str] = field(default_factory=dict)
    # Release-pinned execution policy (reasoner retries, activity timeouts).
    policy: Optional[ExecutionPolicy] = None


def normalize_tool_bindings(bindings: Mapping[str, str]) -> dict[str, str]:
    """Translate config's ``server:tool`` spelling to ToolRef keys."""
    return {
        alias: f"{target.split(':', 1)[0]}/{target.split(':', 1)[1]}"
        for alias, target in bindings.items()
    }


def pipeline_spec_from_ctx(
    config: CtxPipelineConfig,
    *,
    root: Path,
    env_vars: Mapping[str, str] | None = None,
    agent_round_cap: int = 32,
    mcp_servers: Mapping[str, Any] | None = None,
) -> PipelineSpec[Any, Any]:
    ctx_path = Path(config.ctx)
    if not ctx_path.is_absolute():
        ctx_path = root / ctx_path
    merged_env = {**(env_vars or {}), **config.env}
    reasoner = load_dotctx(str(ctx_path), env=merged_env)
    aliases = normalize_tool_bindings(config.tools)
    if reasoner.tools:
        missing = sorted(set(reasoner.tools) - set(aliases))
        extra = sorted(set(aliases) - set(reasoner.tools))
        if missing:
            raise ValueError(
                f"pipeline {config.name!r} has unbound dotctx tool aliases: "
                + ", ".join(missing)
            )
        if extra:
            raise ValueError(
                f"pipeline {config.name!r} binds tools not declared by tools.pyi/settings: "
                + ", ".join(extra)
            )
    elif aliases:
        raise ValueError(
            f"pipeline {config.name!r} binds tools but its dotctx declares no tools"
        )

    snapshot_source = None
    if aliases:
        configured = dict(mcp_servers or {})
        referenced_servers = sorted({wire.split("/", 1)[0] for wire in aliases.values()})
        unknown = sorted(set(referenced_servers) - set(configured))
        if unknown:
            raise ValueError(
                f"pipeline {config.name!r} binds unknown MCP servers: " + ", ".join(unknown)
            )

        selected = {name: configured[name] for name in referenced_servers}

        def snapshot_source(_env: Mapping[str, str]) -> McpSnapshot:
            from .mcp_snapshot import snapshot_servers

            return snapshot_servers(
                selected,
                allowlist=frozenset(server.url for server in selected.values()),
            )

    return PipelineSpec(
        name=config.name,
        flow=reasoner_to_flow(
            reasoner,
            tool_aliases=aliases or None,
            agent_round_cap=agent_round_cap,
        ),
        reasoners=(reasoner,),
        lane=config.lane,
        snapshot_source=snapshot_source,
        execution_policy=config.policy,
    )


__all__ = ["CtxPipelineConfig", "normalize_tool_bindings", "pipeline_spec_from_ctx"]
