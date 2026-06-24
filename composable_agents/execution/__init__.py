"""Temporal-bound execution layer (blueprint, control plane).

Import-safe without ``temporalio``: the deterministic IR interpreter in
:mod:`composable_agents.execution.interpreter` is pure (it takes an injected
:class:`~composable_agents.execution.interpreter.Env` of effect handlers) and has
no Temporal dependency at all, so it is unit-tested in-process. The Temporal
pieces — the ``run`` workflow, the ``callTool`` / ``invokeReasoner`` / ``compilePlan``
activities, the worker, and the OTel exporter — live in sibling modules whose
``temporalio`` import is guarded; importing this package never requires Temporal
to be installed. ``HAVE_TEMPORAL`` says whether it is. The container host shell
in :mod:`composable_agents.execution.serve` (settings, health probes, ``serve``)
is itself import-safe; only calling :func:`serve` needs the ``temporal`` extra.
"""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from typing import Any

from .blobstore import BlobStore, InMemoryBlobStore, content_ref
from .effects import RunPrincipal, WorkerContext, configure
from .interpreter import Env, InMemoryEnv, Result, interpret
from .policy import ExecutionPolicy
from .serve import (
    DEFAULT_TASK_QUEUE,
    HealthServer,
    WorkerServeSettings,
    load_context_factory,
    serve,
)
from .session_store import Cursor, InMemorySessionStore, SessionStore
from .timeouts import activity_timeout

HAVE_TEMPORAL = find_spec("temporalio") is not None
HAVE_DBOS = find_spec("dbos") is not None

_TEMPORAL_EXPORTS = [
    "AgentInput",
    "AgentWorkflow",
    "FlowInput",
    "FlowWorkflow",
    "SessionInput",
    "SessionWorkflow",
    "TemporalSessionHandle",
    "run_flow",
    "start_flow",
    "CallToolInput",
    "CompilePlanInput",
    "InvokeReasonerInput",
    "ResolveQoSInput",
    "callTool",
    "compilePlan",
    "invokeReasoner",
    "resolveAgentSpec",
    "resolveQoS",
    "resolveRuntimeCapabilities",
    "resolveSubflow",
    "verifyPures",
    "build_worker",
    "run_worker",
    "ClaimCheckCodec",
    "claim_check_converter",
    "loadState",
    "commitState",
    "loadValue",
    "commitValue",
    "putBlob",
    "LoadStateInput",
    "CommitStateInput",
    "LoadValueInput",
    "CommitValueInput",
    "PutBlobInput",
]

_TEMPORAL_ATTR_MODULES = {
    "AgentInput": ".harness",
    "AgentWorkflow": ".harness",
    "FlowInput": ".harness",
    "FlowWorkflow": ".harness",
    "SessionInput": ".harness",
    "SessionWorkflow": ".harness",
    "TemporalSessionHandle": ".harness",
    "run_flow": ".harness",
    "start_flow": ".harness",
    "CallToolInput": ".activities",
    "CompilePlanInput": ".activities",
    "InvokeReasonerInput": ".activities",
    "ResolveQoSInput": ".activities",
    "callTool": ".activities",
    "compilePlan": ".activities",
    "invokeReasoner": ".activities",
    "resolveAgentSpec": ".activities",
    "resolveQoS": ".activities",
    "resolveRuntimeCapabilities": ".activities",
    "resolveSubflow": ".activities",
    "verifyPures": ".activities",
    "build_worker": ".worker",
    "run_worker": ".worker",
    "ClaimCheckCodec": ".codec",
    "claim_check_converter": ".worker",
    "loadState": ".activities",
    "commitState": ".activities",
    "loadValue": ".activities",
    "commitValue": ".activities",
    "putBlob": ".activities",
    "LoadStateInput": ".activities",
    "CommitStateInput": ".activities",
    "LoadValueInput": ".activities",
    "CommitValueInput": ".activities",
    "PutBlobInput": ".activities",
}

_DBOS_EXPORTS = [
    "DbosEnv",
    "assert_dbos_executable",
    "decode_policy_error",
    "encode_policy_error",
    "flow_workflow",
    "run_flow_dbos",
    "set_projection_sink",
    "submit_human_dbos",
    "agent_workflow",
    "run_agent_dbos",
]

_DBOS_ATTR_MODULES = {name: ".dbos_backend" for name in _DBOS_EXPORTS}


def __getattr__(name: str) -> Any:
    module_name = _TEMPORAL_ATTR_MODULES.get(name)
    if module_name is not None:
        if not HAVE_TEMPORAL:
            raise AttributeError(name)
    else:
        module_name = _DBOS_ATTR_MODULES.get(name)
        if module_name is None:
            raise AttributeError(name)
        if not HAVE_DBOS:
            raise AttributeError(name)
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


__all__ = [
    "Env",
    "ExecutionPolicy",
    "InMemoryEnv",
    "Result",
    "RunPrincipal",
    "WorkerContext",
    "configure",
    "interpret",
    "activity_timeout",
    "HAVE_TEMPORAL",
    "HAVE_DBOS",
    "BlobStore",
    "InMemoryBlobStore",
    "content_ref",
    "SessionStore",
    "InMemorySessionStore",
    "Cursor",
    "DEFAULT_TASK_QUEUE",
    "HealthServer",
    "WorkerServeSettings",
    "load_context_factory",
    "serve",
] + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else []) + (_DBOS_EXPORTS if HAVE_DBOS else [])
