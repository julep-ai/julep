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

from typing import Any, Optional

from temporalio.client import Client
from temporalio.worker import Worker

from ..capabilities import CapabilityManifest
from .activities import (
    LlmCaller,
    McpCaller,
    WorkerContext,
    callHand,
    compilePlan,
    configure,
    invokeBrain,
    resolveAgentSpec,
    resolveSubflow,
    verifyPures,
)
from .harness import AgentWorkflow, FlowWorkflow

# Every activity the two workflows can dispatch.
ACTIVITIES = [callHand, invokeBrain, compilePlan, verifyPures, resolveSubflow, resolveAgentSpec]
WORKFLOWS = [FlowWorkflow, AgentWorkflow]

DEFAULT_TASK_QUEUE = "composable-agents"


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
    ``(server, tool, value, idempotency_key) -> result``.
    """
    configure(context)
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
    http_timeout_s: float = 30.0,
    **worker_kwargs: Any,
) -> None:
    """Connect to Temporal and run a worker until cancelled (convenience entrypoint).

    This is the batteries-included path for a standalone worker process; for
    finer control (custom client, shared client across workers, lifecycle
    management) use :func:`build_worker` with your own :class:`Client`.
    ``mcp_call`` must be async ``(server, tool, value, idempotency_key) -> result``;
    the idempotency key is the stable activation ``cid`` reused on activity retry.
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
    )
    worker = build_worker(client, context, task_queue=task_queue, **worker_kwargs)
    await worker.run()


__all__ = [
    "ACTIVITIES",
    "WORKFLOWS",
    "DEFAULT_TASK_QUEUE",
    "build_worker",
    "run_worker",
]
