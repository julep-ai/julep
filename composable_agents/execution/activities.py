"""Temporal activity wrappers over the backend-neutral effects layer.

Each activity delegates to :mod:`composable_agents.execution.effects`; the
effect bodies hold all IO and configuration. This module is the only one of
the pair that imports temporalio, so it stays behind the HAVE_TEMPORAL guard.
"""

from __future__ import annotations

from typing import Any

from temporalio import activity

# Re-exports: every public name that previously lived here.
from .effects import (
    CallHandInput as CallHandInput,
    CommitStateInput as CommitStateInput,
    CompilePlanInput as CompilePlanInput,
    InvokeBrainInput as InvokeBrainInput,
    LlmCaller as LlmCaller,
    LoadStateInput as LoadStateInput,
    McpCaller as McpCaller,
    PutBlobInput as PutBlobInput,
    RunPrincipal as RunPrincipal,
    RunSubInput as RunSubInput,
    WorkerContext as WorkerContext,
    configure as configure,
    set_trajectory_sink as set_trajectory_sink,
)
from . import effects


def __getattr__(name: str) -> Any:
    if name == "_CTX":
        return effects._CTX
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


@activity.defn(name="loadState")
async def loadState(inp: LoadStateInput) -> dict[str, Any]:
    return await effects.loadState(inp)


@activity.defn(name="commitState")
async def commitState(inp: CommitStateInput) -> int:
    return await effects.commitState(inp)


@activity.defn(name="putBlob")
async def putBlob(inp: PutBlobInput) -> str:
    return await effects.putBlob(inp)


@activity.defn(name="callHand")
async def callHand(inp: CallHandInput) -> Any:
    return await effects.callHand(inp)


@activity.defn(name="invokeBrain")
async def invokeBrain(inp: InvokeBrainInput) -> Any:
    return await effects.invokeBrain(inp)


@activity.defn(name="compilePlan")
async def compilePlan(inp: CompilePlanInput) -> dict[str, Any]:
    return await effects.compilePlan(inp)


@activity.defn(name="verifyPures")
async def verifyPures(pinned: dict[str, str]) -> None:
    return await effects.verifyPures(pinned)


@activity.defn(name="resolveSubflow")
async def resolveSubflow(ref: str) -> dict[str, Any]:
    return await effects.resolveSubflow(ref)


@activity.defn(name="resolveRuntimeCapabilities")
async def resolveRuntimeCapabilities() -> dict[str, Any]:
    return await effects.resolveRuntimeCapabilities()


@activity.defn(name="resolveAgentSpec")
async def resolveAgentSpec(controller: str) -> dict[str, Any]:
    return await effects.resolveAgentSpec(controller)
