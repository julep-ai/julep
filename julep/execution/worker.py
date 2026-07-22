"""Worker wiring (blueprint §2, control plane host).

A worker is the persistent process that hosts the deterministic workflow code and
executes the activities. There is exactly one workflow type per role
(:class:`~julep.execution.harness.FlowWorkflow` and
:class:`~julep.execution.harness.AgentWorkflow`) and six activities
(startup pure verification, three effect activities, and two deploy-time
resolvers). All
environment-specific configuration — tool URLs, the MCP caller, the LLM client,
the active capability manifest, and the sub-flow / agent registries — is injected
once into the process-global :class:`~julep.execution.activities.WorkerContext`
via :func:`~julep.execution.activities.configure`; the workflows
themselves stay free of it so replay is deterministic.

``temporalio`` is imported at module top, so this module is import-guarded by
:mod:`julep.execution` and only loads where Temporal is present.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, Optional

from temporalio.client import Client
from temporalio.converter import DataConverter, DefaultFailureConverterWithEncodedAttributes
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from ..capabilities import CapabilityManifest
from ..resilience import OnAttempt
from . import anthropic_batch as _anthropic_batch  # noqa: F401 (registers Anthropic BatchProvider)
from . import openai_batch as _openai_batch  # noqa: F401 (registers OpenAI BatchProvider)
from .activities import (
    LlmCaller,
    McpCaller,
    WorkerContext,
    callTool,
    commitState,
    commitValue,
    compilePlan,
    configure,
    invokeReasoner,
    loadState,
    loadValue,
    putBlob,
    resolveAgentSpec,
    resolveQoS,
    resolveRuntimeCapabilities,
    resolveSubflow,
    verifyPures,
)
from .blobstore import BlobStore
from .reasoner_batch import (
    BatchCollector,
    BatchDispatchContext,
    BatchPoll,
    fetchBatchResults,
    install_batch_dispatch_context,
    pollBatch,
    submitBatch,
    submitReasonerBatch,
)
from .bundle_runner import BundleResolvingWorkflowRunner
from .codec import AesGcmPayloadCodec, ClaimCheckCodec, PayloadCodecChain
from .debounce import DebounceCollector
from .harness import (
    AgentWorkflow,
    FlowWorkflow,
    SessionWorkflow,
    finishTrajectory,
    flushStructural,
    runSubCapture,
    startTrajectory,
)
from .projection_store import finalize_projection_run, persist_projection_batch
from .serve import DEFAULT_TASK_QUEUE, payload_encryption_from_env
from .session_store import SessionStore
from ..artifact_store import artifact_store_from_url

# Every activity the two workflows can dispatch.
ACTIVITIES = [
    callTool,
    commitState,
    commitValue,
    invokeReasoner,
    loadState,
    loadValue,
    compilePlan,
    putBlob,
    verifyPures,
    resolveSubflow,
    resolveQoS,
    resolveAgentSpec,
    resolveRuntimeCapabilities,
    startTrajectory,
    finishTrajectory,
    flushStructural,
    runSubCapture,
    persist_projection_batch,
    finalize_projection_run,
    submitReasonerBatch,
    submitBatch,
    pollBatch,
    fetchBatchResults,
]
WORKFLOWS = [
    FlowWorkflow,
    SessionWorkflow,
    AgentWorkflow,
    DebounceCollector,
    BatchCollector,
    BatchPoll,
]


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


def encrypted_payload_converter(
    keys: Mapping[str, bytes | str],
    *,
    active_key_id: str,
    blob_store: Optional[BlobStore] = None,
    tenant: Optional[str] = None,
    threshold_bytes: int = 131072,
) -> DataConverter:
    """Build the shared client/worker converter for encrypted Temporal payloads.

    When a blob store is supplied, claim checking runs first and its small
    pointer is encrypted before reaching Temporal. The referenced S3 object is
    expected to use bucket-level KMS encryption.
    """

    import dataclasses

    encryption = AesGcmPayloadCodec(keys, active_key_id=active_key_id)
    if blob_store is None:
        codec = encryption
    else:
        if tenant is None or not tenant:
            raise ValueError("tenant is required when blob_store is provided")
        codec = PayloadCodecChain(
            [
                ClaimCheckCodec(
                    blob_store,
                    tenant=tenant,
                    threshold_bytes=threshold_bytes,
                ),
                encryption,
            ]
        )
    return dataclasses.replace(
        DataConverter.default,
        payload_codec=codec,
        failure_converter_class=DefaultFailureConverterWithEncodedAttributes,
    )


def build_worker(
    client: Client,
    context: WorkerContext,
    *,
    task_queue: str = DEFAULT_TASK_QUEUE,
    min_batch_window_s: float = 0.0,
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

    The default workflow sandbox passes ``julep`` through so
    workflow-side registry lookups (pures, reasoners) see the worker process's real
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
    install_batch_dispatch_context(
        BatchDispatchContext(
            client=client,
            task_queue=task_queue,
            min_batch_window_s=min_batch_window_s,
        )
    )
    if "workflow_runner" not in worker_kwargs:
        store_url = os.environ.get("JULEP_ARTIFACT_STORE_URL", "").strip()
        store = artifact_store_from_url(store_url) if store_url else None
        worker_kwargs["workflow_runner"] = BundleResolvingWorkflowRunner(
            inner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default.with_passthrough_modules(
                    "julep",
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
    tool_urls: Optional[dict[str, str]] = None,
    mcp_call: Optional[McpCaller] = None,
    llm: Optional[LlmCaller] = None,
    capabilities: Optional[CapabilityManifest] = None,
    subflows: Optional[dict[str, dict]] = None,
    agents: Optional[dict[str, dict]] = None,
    blob_store: Optional[BlobStore] = None,
    session_store: Optional[SessionStore] = None,
    trajectory_sink: Optional[Any] = None,
    trajectory_blob_store: Optional[BlobStore] = None,
    on_attempt: Optional[OnAttempt] = None,
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
    connect_kwargs: dict[str, Any] = {"namespace": namespace}
    payload_keys, payload_key_id, _required = payload_encryption_from_env(os.environ)
    if payload_keys is not None:
        from .codec import parse_aes_gcm_keyring
        from .trace_headers import WorkflowTraceHeadersInterceptor
        from temporalio.common import HeaderCodecBehavior

        assert payload_key_id is not None
        connect_kwargs["data_converter"] = encrypted_payload_converter(
            parse_aes_gcm_keyring(payload_keys),
            active_key_id=payload_key_id,
        )
        connect_kwargs["header_codec_behavior"] = HeaderCodecBehavior.CODEC
        connect_kwargs["interceptors"] = [WorkflowTraceHeadersInterceptor()]
    client = await Client.connect(target_host, **connect_kwargs)
    context = WorkerContext(
        tool_urls=tool_urls or {},
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
        on_attempt=on_attempt,
    )
    worker = build_worker(client, context, task_queue=task_queue, **worker_kwargs)
    await worker.run()


__all__ = [
    "ACTIVITIES",
    "WORKFLOWS",
    "DEFAULT_TASK_QUEUE",
    "build_worker",
    "claim_check_converter",
    "encrypted_payload_converter",
    "run_worker",
]
