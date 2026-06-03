"""Temporal-bound execution layer (blueprint, control plane).

Import-safe without ``temporalio``: the deterministic IR interpreter in
:mod:`composable_agents.execution.interpreter` is pure (it takes an injected
:class:`~composable_agents.execution.interpreter.Env` of effect handlers) and has
no Temporal dependency at all, so it is unit-tested in-process. The Temporal
pieces — the ``run`` workflow, the ``callHand`` / ``invokeBrain`` / ``compilePlan``
activities, the worker, and the OTel exporter — live in sibling modules whose
``temporalio`` import is guarded; importing this package never requires Temporal
to be installed. ``HAVE_TEMPORAL`` says whether it is.
"""

from __future__ import annotations

from .interpreter import Env, InMemoryEnv, Result, interpret

try:  # the workflow/activities only import cleanly with temporalio present
    from .harness import (  # noqa: F401
        AgentInput,
        AgentWorkflow,
        ExecutionPolicy,
        FlowInput,
        FlowWorkflow,
        run_flow,
        start_flow,
    )
    from .activities import (  # noqa: F401
        CallHandInput,
        CompilePlanInput,
        InvokeBrainInput,
        WorkerContext,
        callHand,
        compilePlan,
        configure,
        invokeBrain,
        resolveAgentSpec,
        resolveSubflow,
    )
    from .worker import build_worker, run_worker  # noqa: F401

    HAVE_TEMPORAL = True
except ModuleNotFoundError:
    HAVE_TEMPORAL = False

_TEMPORAL_EXPORTS = [
    "AgentInput",
    "AgentWorkflow",
    "ExecutionPolicy",
    "FlowInput",
    "FlowWorkflow",
    "run_flow",
    "start_flow",
    "CallHandInput",
    "CompilePlanInput",
    "InvokeBrainInput",
    "WorkerContext",
    "callHand",
    "compilePlan",
    "configure",
    "invokeBrain",
    "resolveAgentSpec",
    "resolveSubflow",
    "build_worker",
    "run_worker",
]

__all__ = [
    "Env",
    "InMemoryEnv",
    "Result",
    "interpret",
    "HAVE_TEMPORAL",
] + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else [])
