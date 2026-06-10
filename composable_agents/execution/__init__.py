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

from .blobstore import BlobStore, InMemoryBlobStore, content_ref
from .interpreter import Env, InMemoryEnv, Result, interpret
from .session_store import Cursor, InMemorySessionStore, SessionStore
from .timeouts import activity_timeout

HAVE_TEMPORAL = find_spec("temporalio") is not None
HAVE_DBOS = find_spec("dbos") is not None

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
    "ClaimCheckCodec",
    "claim_check_converter",
    "loadState",
    "commitState",
    "putBlob",
    "LoadStateInput",
    "CommitStateInput",
    "PutBlobInput",
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
    "ClaimCheckCodec": ".codec",
    "claim_check_converter": ".worker",
    "loadState": ".activities",
    "commitState": ".activities",
    "putBlob": ".activities",
    "LoadStateInput": ".activities",
    "CommitStateInput": ".activities",
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
    "InMemoryEnv",
    "Result",
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
] + (_TEMPORAL_EXPORTS if HAVE_TEMPORAL else []) + (_DBOS_EXPORTS if HAVE_DBOS else [])
