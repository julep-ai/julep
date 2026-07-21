"""Local single-shot runner for dotctx packages."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping

from julep.cli import evalrun
from julep.deploy import deploy
from julep.dotctx import load_dotctx, reasoner_to_flow
from julep.freeze import McpSnapshot


@dataclass(frozen=True)
class CtxRunOutcome:
    artifact_hash: str
    reply: Any


def run_ctx_local(
    ctx_path: str,
    value: Any,
    *,
    env_vars: Mapping[str, str] | None = None,
    acompletion: Any = None,
    llm_caller: Any = None,
) -> CtxRunOutcome:
    reasoner = load_dotctx(ctx_path, env=dict(env_vars or {}))
    deployment = deploy(
        reasoner_to_flow(reasoner),
        snapshot=McpSnapshot(servers={}),
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
    reply = asyncio.run(
        evalrun._invoke_eval_llm(
            reasoner,
            value,
            acompletion=resolved,
            llm_caller=llm_caller,
        )
    )
    return CtxRunOutcome(artifact_hash=deployment.artifact_hash, reply=reply)


__all__ = ["CtxRunOutcome", "run_ctx_local"]
