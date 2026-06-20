"""Worker wiring (blueprint §2, control plane host).

A worker is the persistent process that hosts the deterministic workflow code and
executes the activities. There is exactly one workflow type per role
(:class:`~composable_agents.execution.harness.FlowWorkflow` and
:class:`~composable_agents.execution.harness.AgentWorkflow`) and six activities
(startup pure verification, three effect activities, and two deploy-time
resolvers). All
environment-specific configuration — hand URLs, the MCP caller, the LLM client,
the active capability manifest, and the sub-flow / agent registries — is injected
once into the process-global :class:`~composable_agents.execution.activities.WorkerContext`
via :func:`~composable_agents.execution.activities.configure`; the workflows
themselves stay free of it so replay is deterministic.

``temporalio`` is imported at module top, so this module is import-guarded by
:mod:`composable_agents.execution` and only loads where Temporal is present.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from temporalio.client import Client
from temporalio.converter import DataConverter
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from ..capabilities import CapabilityManifest
from .activities import (
    LlmCaller,
    McpCaller,
    WorkerContext,
    callHand,
    commitState,
    compilePlan,
    configure,
    invokeBrain,
    loadState,
    putBlob,
    resolveAgentSpec,
    resolveRuntimeCapabilities,
    resolveSubflow,
    verifyPures,
)
from .blobstore import BlobStore
from .bundle_runner import BundleResolvingWorkflowRunner
from .codec import ClaimCheckCodec
from .debounce import DebounceCollector
from .harness import AgentWorkflow, FlowWorkflow, finishTrajectory, runSubCapture
from .serve import DEFAULT_TASK_QUEUE
from .session_store import SessionStore
from ..cas import cas_from_url

# Every activity the two workflows can dispatch.
ACTIVITIES = [
    callHand,
    commitState,
    invokeBrain,
    loadState,
    compilePlan,
    putBlob,
    verifyPures,
    resolveSubflow,
    resolveAgentSpec,
    resolveRuntimeCapabilities,
    finishTrajectory,
    runSubCapture,
]
WORKFLOWS = [FlowWorkflow, AgentWorkflow, DebounceCollector]


def claim_check_converter(
    blob_store: BlobStore,
    *,
    tenant: str,
    threshold_bytes: int = 131072,
) -> DataConverter:
    """A DataConverter that offloads oversized payloads via ClaimCheckCodec.

    Pass this as ``data_converter=`` when CONNECTING the Temporal Client; the
    worker inherits it from the client. Temporal enforces its size limits on the
    post-codec payload.
    """
    import dataclasses

    return dataclasses.replace(
        DataConverter.default,
        payload_codec=ClaimCheckCodec(
            blob_store, tenant=tenant, threshold_bytes=threshold_bytes
        ),
    )


def build_worker(
    client: Client,
    context: WorkerContext,
    *,
    task_queue: str = DEFAULT_TASK_QUEUE,
    **worker_kwargs: Any,
) -> Worker:
    """Install ``context`` and return a :class:`Worker` registered for everything.

    The caller owns the ``client`` (so connection, namespace, TLS and data
    converter are its concern) and the returned worker (so it controls
    ``async with worker`` / ``await worker.run()`` and shutdown). Extra
    ``worker_kwargs`` pass straight through to :class:`temporalio.worker.Worker`
    (e.g. ``max_concurrent_activities``, ``interceptors`` for the projection tail).
    If ``context.mcp_call`` is set, it must be async
    ``(server, tool, value, idempotency_key, principal) -> result``; legacy
    4-argument callers are wrapped by ``configure`` and keep working.

    The default workflow sandbox passes ``composable_agents`` through so
    workflow-side registry lookups (pures, brains) see the worker process's real
    registries; without it, sandbox re-imports yield empty registries and flows
    with ``arr``/registry-dependent leaves hang in a WorkflowTaskFailed retry
    loop. It also passes ``wasmtime`` through so bundle-sourced
    (``tier="wasm"``) pures invoked synchronously inside workflow code share the
    worker process-global wasmtime ``Engine`` and compiled ``Component``; the
    wasm executor is process-global and lazily initialized. Without it, the
    sandbox would re-import ``wasmtime`` and the workflow-side wasm pure call
    would not share that process-global engine/component. Pass your own
    ``workflow_runner`` to override.
    """
    configure(context)
    if "workflow_runner" not in worker_kwargs:
        store_url = os.environ.get("STORE_URL", "").strip()
        store = cas_from_url(store_url) if store_url else None
        worker_kwargs["workflow_runner"] = BundleResolvingWorkflowRunner(
            inner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default.with_passthrough_modules(
                    "composable_agents",
                    "wasmtime",
                )
            ),
            store=store,
        )
    return Worker(
        client,
        task_queue=task_queue,
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
        **worker_kwargs,
    )


async def run_worker(
    *,
    target_host: str = "localhost:7233",
    namespace: str = "default",
    task_queue: str = DEFAULT_TASK_QUEUE,
    hand_urls: Optional[dict[str, str]] = None,
    mcp_call: Optional[McpCaller] = None,
    llm: Optional[LlmCaller] = None,
    capabilities: Optional[CapabilityManifest] = None,
    subflows: Optional[dict[str, dict]] = None,
    agents: Optional[dict[str, dict]] = None,
    blob_store: Optional[BlobStore] = None,
    session_store: Optional[SessionStore] = None,
    trajectory_sink: Optional[Any] = None,
    trajectory_blob_store: Optional[BlobStore] = None,
    http_timeout_s: float = 30.0,
    **worker_kwargs: Any,
) -> None:
    """Connect to Temporal and run a worker until cancelled (convenience entrypoint).

    This is the batteries-included path for a standalone worker process; for
    finer control (custom client, shared client across workers, lifecycle
    management) use :func:`build_worker` with your own :class:`Client`.
    ``mcp_call`` must be async
    ``(server, tool, value, idempotency_key, principal) -> result`` (legacy
    4-argument callers are wrapped by ``configure``); the idempotency key is the
    stable activation ``cid`` reused on activity retry.
    """
    client = await Client.connect(target_host, namespace=namespace)
    context = WorkerContext(
        hand_urls=hand_urls or {},
        mcp_call=mcp_call,
        llm=llm,
        capabilities=capabilities,
        http_timeout_s=http_timeout_s,
        subflows=subflows or {},
        agents=agents or {},
        blob_store=blob_store,
        session_store=session_store,
        trajectory_sink=trajectory_sink,
        trajectory_blob_store=trajectory_blob_store,
    )
    worker = build_worker(client, context, task_queue=task_queue, **worker_kwargs)
    await worker.run()


__all__ = [
    "ACTIVITIES",
    "WORKFLOWS",
    "DEFAULT_TASK_QUEUE",
    "build_worker",
    "claim_check_converter",
    "run_worker",
]
