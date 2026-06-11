"""Worker serve entrypoint: env settings, factory loading, health probes, drain.

Settings parsing, factory resolution, and the probe listener are pure stdlib
and run everywhere. The lifecycle test (connect, poll, drain on shutdown) needs
``temporalio`` and the time-skipping test server.
"""

from __future__ import annotations

import asyncio

import pytest

from composable_agents import HAVE_TEMPORAL
from composable_agents.errors import ComposableAgentsError
from composable_agents.execution.effects import WorkerContext
from composable_agents.execution.serve import (
    DEFAULT_TASK_QUEUE,
    HealthServer,
    WorkerServeSettings,
    load_context_factory,
    serve,
)
from conftest import run


# --------------------------------------------------------------------------- #
# Settings from the environment.
# --------------------------------------------------------------------------- #
def test_from_env_requires_context_factory():
    with pytest.raises(ValueError, match="WORKER_CONTEXT_FACTORY"):
        WorkerServeSettings.from_env({})


def test_from_env_defaults():
    s = WorkerServeSettings.from_env({"WORKER_CONTEXT_FACTORY": "m:f"})
    assert s.context_factory == "m:f"
    assert s.address == "localhost:7233"
    assert s.namespace == "default"
    assert s.task_queue == DEFAULT_TASK_QUEUE == "composable-agents"
    assert s.api_key is None and s.tls is False
    assert s.graceful_shutdown_s == 30.0
    assert s.max_concurrent_activities is None
    assert s.max_concurrent_workflow_tasks is None
    assert s.health_port is None


def test_from_env_full_parse():
    s = WorkerServeSettings.from_env({
        "WORKER_CONTEXT_FACTORY": "pkg.mod:make",
        "TEMPORAL_ADDRESS": "temporal-frontend.temporal.svc:7233",
        "TEMPORAL_NAMESPACE": "prod",
        "TEMPORAL_TASK_QUEUE": "lane-embeddings",
        "WORKER_GRACEFUL_SHUTDOWN_S": "12.5",
        "WORKER_MAX_CONCURRENT_ACTIVITIES": "16",
        "WORKER_MAX_CONCURRENT_WORKFLOW_TASKS": "8",
        "WORKER_HEALTH_PORT": "8080",
    })
    assert s.address == "temporal-frontend.temporal.svc:7233"
    assert s.namespace == "prod"
    assert s.task_queue == "lane-embeddings"
    assert s.graceful_shutdown_s == 12.5
    assert s.max_concurrent_activities == 16
    assert s.max_concurrent_workflow_tasks == 8
    assert s.health_port == 8080


def test_api_key_implies_tls_unless_overridden():
    base = {"WORKER_CONTEXT_FACTORY": "m:f", "TEMPORAL_API_KEY": "k"}
    assert WorkerServeSettings.from_env(base).tls is True
    s = WorkerServeSettings.from_env({**base, "TEMPORAL_TLS": "false"})
    assert s.tls is False and s.api_key == "k"
    s = WorkerServeSettings.from_env({"WORKER_CONTEXT_FACTORY": "m:f", "TEMPORAL_TLS": "ON"})
    assert s.tls is True


def test_bad_env_values_fail_loudly():
    base = {"WORKER_CONTEXT_FACTORY": "m:f"}
    with pytest.raises(ValueError, match="TEMPORAL_TLS"):
        WorkerServeSettings.from_env({**base, "TEMPORAL_TLS": "banana"})
    with pytest.raises(ValueError, match="WORKER_HEALTH_PORT"):
        WorkerServeSettings.from_env({**base, "WORKER_HEALTH_PORT": "eighty"})
    with pytest.raises(ValueError, match="WORKER_GRACEFUL_SHUTDOWN_S"):
        WorkerServeSettings.from_env({**base, "WORKER_GRACEFUL_SHUTDOWN_S": "soon"})


# --------------------------------------------------------------------------- #
# Context factory resolution.
# --------------------------------------------------------------------------- #
def make_context() -> WorkerContext:
    """Module-level factory used through its `module:attr` spec."""

    async def _mcp(server, tool, value, idempotency_key):
        assert tool == "inc"
        return value + 1

    return WorkerContext(mcp_call=_mcp)


def not_a_factory() -> str:
    return "nope"


NOT_CALLABLE = object()


def test_load_context_factory_resolves_module_attr():
    factory = load_context_factory(f"{__name__}:make_context")
    assert isinstance(factory(), WorkerContext)


def test_load_context_factory_rejects_bad_specs():
    with pytest.raises(ValueError, match="module:attr"):
        load_context_factory("no_colon")
    with pytest.raises(ValueError, match="cannot import"):
        load_context_factory("definitely.not.a.module:make")
    with pytest.raises(ValueError, match="no attribute"):
        load_context_factory(f"{__name__}:missing_factory")
    with pytest.raises(ValueError, match="not callable"):
        load_context_factory(f"{__name__}:NOT_CALLABLE")


def test_serve_rejects_factory_returning_wrong_type():
    settings = WorkerServeSettings(context_factory=f"{__name__}:not_a_factory")
    if not HAVE_TEMPORAL:
        with pytest.raises(ComposableAgentsError, match="temporal"):
            run(serve(settings))
        return
    with pytest.raises(ComposableAgentsError, match="must return a WorkerContext"):
        run(serve(settings))


# --------------------------------------------------------------------------- #
# Health probe listener.
# --------------------------------------------------------------------------- #
async def _get_status(port: int, path: str) -> int:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(f"GET {path} HTTP/1.1\r\nHost: probe\r\n\r\n".encode())
    await writer.drain()
    status_line = await reader.readline()
    writer.close()
    await writer.wait_closed()
    return int(status_line.split()[1])


async def _health_probe_lifecycle():
    health = HealthServer(0, host="127.0.0.1")
    await health.start()
    try:
        port = health.port
        assert await _get_status(port, "/healthz") == 200
        assert await _get_status(port, "/readyz") == 503  # not polling yet
        health.ready = True
        assert await _get_status(port, "/readyz") == 200
        health.ready = False  # drain started
        assert await _get_status(port, "/readyz") == 503
        assert await _get_status(port, "/healthz") == 200  # liveness unaffected
        assert await _get_status(port, "/metrics") == 404
    finally:
        await health.stop()


def test_health_server_probes():
    run(_health_probe_lifecycle())


# --------------------------------------------------------------------------- #
# Lifecycle against the time-skipping server: poll, execute, drain on shutdown.
# --------------------------------------------------------------------------- #
async def _serve_lifecycle():
    from temporalio.testing import WorkflowEnvironment

    from composable_agents import call, freeze, manifest_to_json, mcp
    from composable_agents.contracts import McpAnnotations
    from composable_agents.execution.harness import run_flow
    from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec

    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    snapshot = McpSnapshot(servers={"srv": McpServerSnapshot(server="srv", version="1", tools={
        "inc": McpToolSpec(input_schema={}, annotations=ann),
    })})
    fr = freeze(call(mcp("srv", "inc")), snapshot)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        settings = WorkerServeSettings(
            context_factory=f"{__name__}:make_context",
            address=env.client.service_client.config.target_host,
            task_queue="ca-serve",
            graceful_shutdown_s=5.0,
        )
        stop = asyncio.Event()
        serve_task = asyncio.create_task(serve(settings, shutdown_event=stop))
        try:
            out = await run_flow(
                env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                session_id="serve-1", input=2, task_queue="ca-serve",
            )
            assert out == 3, out  # the served worker polled and executed
        finally:
            stop.set()
        await asyncio.wait_for(serve_task, timeout=30)  # drains and returns


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_serve_lifecycle_end_to_end():
    asyncio.run(asyncio.wait_for(_serve_lifecycle(), timeout=120))


@pytest.mark.skipif(HAVE_TEMPORAL, reason="exercises the missing-extra error")
def test_serve_without_temporalio_fails_explicitly():
    settings = WorkerServeSettings(context_factory=f"{__name__}:make_context")
    with pytest.raises(ComposableAgentsError, match="composable-agents\\[temporal\\]"):
        run(serve(settings))
