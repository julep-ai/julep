"""Configuration-backed dotctx application pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .app import PipelineSpec
from .dotctx import load_dotctx, reasoner_to_flow


@dataclass(frozen=True)
class CtxPipelineConfig:
    name: str
    ctx: str
    lane: str = "default"
    env: dict[str, str] = field(default_factory=dict)


def pipeline_spec_from_ctx(
    config: CtxPipelineConfig,
    *,
    root: Path,
    env_vars: Mapping[str, str] | None = None,
) -> PipelineSpec[Any, Any]:
    ctx_path = Path(config.ctx)
    if not ctx_path.is_absolute():
        ctx_path = root / ctx_path
    merged_env = {**(env_vars or {}), **config.env}
    reasoner = load_dotctx(str(ctx_path), env=merged_env)
    return PipelineSpec(
        name=config.name,
        flow=reasoner_to_flow(reasoner),
        reasoners=(reasoner,),
        lane=config.lane,
    )


__all__ = ["CtxPipelineConfig", "pipeline_spec_from_ctx"]
