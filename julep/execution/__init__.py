"""Temporal-bound execution layer (blueprint, control plane).

Import-safe without ``temporalio``: the deterministic IR interpreter in
:mod:`julep.execution.interpreter` is pure (it takes an injected
:class:`~julep.execution.interpreter.Env` of effect handlers) and has
no Temporal dependency at all, so it is unit-tested in-process. The Temporal
pieces — the ``run`` workflow, the ``callTool`` / ``invokeReasoner`` / ``compilePlan``
activities, the worker, and the OTel exporter — live in sibling modules whose
``temporalio`` import is guarded; importing this package never requires Temporal
to be installed. ``HAVE_TEMPORAL`` says whether it is. The container host shell
in :mod:`julep.execution.serve` (settings, health probes, ``serve``)
is itself import-safe; only calling :func:`serve` needs the ``temporal`` extra.
"""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .cma_session import CMASessionHandle as CMASessionHandle

from .blobstore import (
    BlobStore,
    InMemoryBlobStore,
    LocalDirBlobStore,
    blob_store_from_url,
    content_ref,
)
from .effects import LlmCaller, RunPrincipal, WorkerContext, configure
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
    "AesGcmPayloadCodec",
    "PayloadCodecChain",
    "claim_check_converter",
    "encrypted_payload_converter",
    "WorkflowTraceHeadersInterceptor",
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
    "AesGcmPayloadCodec": ".codec",
    "PayloadCodecChain": ".codec",
    "claim_check_converter": ".worker",
    "encrypted_payload_converter": ".worker",
    "WorkflowTraceHeadersInterceptor": ".trace_headers",
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
    if name == "CMASessionHandle":
        module = import_module(".cma_session", __name__)
        value = module.CMASessionHandle
        globals()[name] = value
        return value
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
    "LlmCaller",
    "RunPrincipal",
    "WorkerContext",
    "configure",
    "interpret",
    "activity_timeout",
    "HAVE_TEMPORAL",
    "HAVE_DBOS",
    "BlobStore",
    "InMemoryBlobStore",
    "LocalDirBlobStore",
    "blob_store_from_url",
    "content_ref",
    "CMASessionHandle",
    "SessionStore",
    "InMemorySessionStore",
    "Cursor",
    "DEFAULT_TASK_QUEUE",
    "HealthServer",
    "WorkerServeSettings",
    "load_context_factory",
    "serve",
] + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else []) + (_DBOS_EXPORTS if HAVE_DBOS else [])
