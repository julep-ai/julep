"""Local single-shot runner for dotctx packages."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Mapping

from julep.cli import evalrun
from julep.deploy import deploy
from julep.dotctx import load_dotctx, reasoner_to_flow
from julep.dotctx_rich import load_rich_dotctx
from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from julep.projection import InMemoryProjection, ProjectionSink


@dataclass(frozen=True)
class CtxRunOutcome:
    artifact_hash: str
    reply: Any
    projection: InMemoryProjection = field(default_factory=InMemoryProjection)


def run_ctx_local(
    ctx_path: str,
    value: Any,
    *,
    env_vars: Mapping[str, str] | None = None,
    acompletion: Any = None,
    llm_caller: Any = None,
    tools: Mapping[str, Callable[[Any], Any]] | None = None,
    tool_bindings: Mapping[str, str] | None = None,
    mcp_call: Any = None,
    projection: InMemoryProjection | None = None,
    sink: ProjectionSink | None = None,
) -> CtxRunOutcome:
    reasoner = load_dotctx(ctx_path, env=dict(env_vars or {}))
    if reasoner.tools:
        rich = load_rich_dotctx(ctx_path, env=dict(env_vars or {}))
        aliases = dict(
            tool_bindings
            or {name: f"local/{name}" for name in reasoner.tools}
        )
        missing = sorted(set(reasoner.tools) - set(aliases))
        if missing:
            raise ValueError("unbound local tool aliases: " + ", ".join(missing))
        servers: dict[str, McpServerSnapshot] = {}
        grouped: dict[str, dict[str, McpToolSpec]] = {}
        for alias, wire in aliases.items():
            server, separator, tool = wire.partition("/")
            if separator != "/" or not server or not tool:
                raise ValueError(f"tool binding {alias!r} must use 'server/tool'")
            grouped.setdefault(server, {})[tool] = McpToolSpec(
                input_schema=rich.expected_tool_schemas[alias]
            )
        for server, specs in grouped.items():
            servers[server] = McpServerSnapshot(server=server, tools=specs)
        snapshot = McpSnapshot(servers=servers)
        flow = reasoner_to_flow(reasoner, tool_aliases=aliases)
    else:
        rich = None
        snapshot = McpSnapshot(servers={})
        flow = reasoner_to_flow(reasoner)
    deployment = deploy(
        flow,
        snapshot=snapshot,
        reasoners=[reasoner],
    )
    resolved = (
        acompletion
        if acompletion is not None
        else (
            None
            if llm_caller is not None
            else evalrun._resolve_acompletion(None)
        )
    )
    tool_defs = None
    if rich is not None:
        tool_defs = evalrun._provider_tool_defs(
            rich.expected_tool_schemas,
            rich.expected_tool_descriptions,
        )

    async def controller(payload: Any) -> Any:
        return await evalrun._invoke_eval_llm(
            reasoner,
            payload,
            acompletion=resolved,
            llm_caller=llm_caller,
            tools=tool_defs,
        )

    # AIDEV-NOTE: even single-shot .ctx packages must traverse the interpreter;
    # bypassing it produces no projection and makes the local trace cache blind.
    local_deployment = (
        deployment if rich is not None else replace(deployment, _tools=())
    )
    run_projection = projection if projection is not None else InMemoryProjection()
    reply = asyncio.run(
        local_deployment.adry_run(
            value,
            reasoners={reasoner.name: controller},
            tools=dict(tools or {}),
            mcp_call=mcp_call,
            projection=run_projection,
            sink=sink,
        )
    ).value
    return CtxRunOutcome(
        artifact_hash=deployment.artifact_hash,
        reply=reply,
        projection=run_projection,
    )


__all__ = ["CtxRunOutcome", "run_ctx_local"]
