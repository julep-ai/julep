"""Public helpers for compiling and running standalone dotctx pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional

from .cli.config import McpServerConfig
from .ctx_pipeline import CtxPipelineConfig, pipeline_spec_from_ctx
from .execution.effects import WorkerContext
from .execution.policy import ExecutionPolicy
from .local import (
    EmbeddedRun,
    LocalExecutionUnsupported,
    LocalPipeline,
    LocalPipelineNotFound,
    _local_pipeline_from_spec,
    prepare_local_pipeline,
)


def load_pipeline(
    path: str | Path,
    *,
    env: Optional[Mapping[str, str]] = None,
    name: Optional[str] = None,
    tools: Optional[Mapping[str, str]] = None,
    policy: Optional[ExecutionPolicy] = None,
    mcp_servers: Optional[Mapping[str, McpServerConfig]] = None,
) -> LocalPipeline:
    """Compile one dotctx package without a project file or control-plane naming.

    ``tools`` maps prompt-visible MCP aliases to ``server:tool`` targets. The
    resolved package is compiled under the stable application name ``embedded``.
    """
    resolved = Path(path).expanduser().resolve()
    config = CtxPipelineConfig(
        name=name if name is not None else resolved.stem,
        ctx=str(resolved),
        env=dict(env or {}),
        tools=dict(tools or {}),
        policy=policy,
    )
    spec = pipeline_spec_from_ctx(
        config,
        root=resolved.parent,
        env_vars=env,
        mcp_servers=mcp_servers,
    )
    return _local_pipeline_from_spec(
        spec,
        application_name="embedded",
        environment="embedded",
        env_vars=dict(env or {}),
    )


__all__ = [
    "EmbeddedRun",
    "LocalExecutionUnsupported",
    "LocalPipeline",
    "LocalPipelineNotFound",
    "WorkerContext",
    "load_pipeline",
    "prepare_local_pipeline",
]
