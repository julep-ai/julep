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

from importlib import import_module
from importlib.util import find_spec
from typing import Any

from .interpreter import Env, InMemoryEnv, Result, interpret
from .timeouts import activity_timeout

HAVE_TEMPORAL = find_spec("temporalio") is not None

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
    "resolveRuntimeCapabilities",
    "resolveSubflow",
    "verifyPures",
    "build_worker",
    "run_worker",
]

_TEMPORAL_ATTR_MODULES = {
    "AgentInput": ".harness",
    "AgentWorkflow": ".harness",
    "ExecutionPolicy": ".harness",
    "FlowInput": ".harness",
    "FlowWorkflow": ".harness",
    "run_flow": ".harness",
    "start_flow": ".harness",
    "CallHandInput": ".activities",
    "CompilePlanInput": ".activities",
    "InvokeBrainInput": ".activities",
    "WorkerContext": ".activities",
    "callHand": ".activities",
    "compilePlan": ".activities",
    "configure": ".activities",
    "invokeBrain": ".activities",
    "resolveAgentSpec": ".activities",
    "resolveRuntimeCapabilities": ".activities",
    "resolveSubflow": ".activities",
    "verifyPures": ".activities",
    "build_worker": ".worker",
    "run_worker": ".worker",
}


def __getattr__(name: str) -> Any:
    module_name = _TEMPORAL_ATTR_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    if not HAVE_TEMPORAL:
        raise AttributeError(name)
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "Env",
    "InMemoryEnv",
    "Result",
    "interpret",
    "activity_timeout",
    "HAVE_TEMPORAL",
] + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else [])
