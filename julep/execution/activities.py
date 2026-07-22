"""Temporal activity wrappers over the backend-neutral effects layer.

Each activity delegates to :mod:`julep.execution.effects`; the
effect bodies hold all IO and configuration. This module is the only one of
the pair that imports temporalio, so it stays behind the HAVE_TEMPORAL guard.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from temporalio import activity

# Re-exports: every public name that previously lived here.
from .effects import (
    CallToolInput as CallToolInput,
    CommitStateInput as CommitStateInput,
    CommitValueInput as CommitValueInput,
    CompilePlanInput as CompilePlanInput,
    InvokeReasonerInput as InvokeReasonerInput,
    LlmCaller as LlmCaller,
    LoadStateInput as LoadStateInput,
    LoadValueInput as LoadValueInput,
    McpCaller as McpCaller,
    PutBlobInput as PutBlobInput,
    ResolveQoSInput as ResolveQoSInput,
    ResolveAgentSpecInput as ResolveAgentSpecInput,
    RunPrincipal as RunPrincipal,
    RunSubInput as RunSubInput,
    VerifyPuresInput as VerifyPuresInput,
    ValidateAgentOutputInput as ValidateAgentOutputInput,
    ValidateJsonSchemaInput as ValidateJsonSchemaInput,
    WorkerContext as WorkerContext,
    configure as configure,
    set_trajectory_sink as set_trajectory_sink,
)
from . import effects
from .failure_scrub import activity_application_error_from_failure


_T = TypeVar("_T")


async def _run_secret_safe(
    inp: Any,
    effect: Callable[[Any], Awaitable[_T]],
) -> _T:
    """Keep an activity failure's original run-secret echo out of history."""

    try:
        return await effect(inp)
    except Exception as exc:
        secrets = getattr(inp, "secrets", None)
        # ``from None`` is essential: Temporal serializes exception causes.
        raise activity_application_error_from_failure(exc, secrets) from None


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


@activity.defn(name="loadValue")
async def loadValue(inp: LoadValueInput) -> Any:
    return await effects.loadValue(inp)


@activity.defn(name="commitValue")
async def commitValue(inp: CommitValueInput) -> int:
    return await effects.commitValue(inp)


@activity.defn(name="putBlob")
async def putBlob(inp: PutBlobInput) -> str:
    return await _run_secret_safe(inp, effects.putBlob)


@activity.defn(name="callTool")
async def callTool(inp: CallToolInput) -> Any:
    return await _run_secret_safe(inp, effects.callTool)


@activity.defn(name="invokeReasoner")
async def invokeReasoner(inp: InvokeReasonerInput) -> Any:
    return await _run_secret_safe(inp, effects.invokeReasoner)


@activity.defn(name="compilePlan")
async def compilePlan(inp: CompilePlanInput) -> dict[str, Any]:
    # Planner/provider failures can reflect operator credentials even though
    # CompilePlanInput intentionally carries no run-secret map.
    return await _run_secret_safe(inp, effects.compilePlan)


@activity.defn(name="verifyPures")
async def verifyPures(inp: Any) -> None:
    return await effects.verifyPures(inp)


@activity.defn(name="resolveSubflow")
async def resolveSubflow(ref: str) -> dict[str, Any]:
    return await effects.resolveSubflow(ref)


@activity.defn(name="resolveQoS")
async def resolveQoS(inp: ResolveQoSInput) -> str:
    return await effects.resolveQoS(inp)


@activity.defn(name="resolveRuntimeCapabilities")
async def resolveRuntimeCapabilities() -> dict[str, Any]:
    return await effects.resolveRuntimeCapabilities()


@activity.defn(name="resolveAgentSpec")
async def resolveAgentSpec(inp: ResolveAgentSpecInput | str) -> dict[str, Any]:
    return await effects.resolveAgentSpec(inp)


@activity.defn(name="validateAgentOutput")
async def validateAgentOutput(inp: ValidateAgentOutputInput) -> str | None:
    return await effects.validateAgentOutput(inp)


@activity.defn(name="validateJsonSchema")
async def validateJsonSchema(inp: ValidateJsonSchemaInput) -> str | None:
    return await effects.validateJsonSchema(inp)
