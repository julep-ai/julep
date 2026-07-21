"""Worker serve entrypoint: env settings, factory loading, health probes, drain.

Settings parsing, factory resolution, and the probe listener are pure stdlib
and run everywhere. The lifecycle test (connect, poll, drain on shutdown) needs
``temporalio`` and the time-skipping test server.
"""

from __future__ import annotations

import asyncio
import sys
import types
import warnings
from importlib import import_module
from typing import Any

import pytest

from julep import HAVE_TEMPORAL, __version__
from julep.errors import JulepError
from julep.app import Application, ApplicationDefinitionError, PipelineSpec
from julep.dotctx import Reasoner
from julep.dsl import think
from julep.execution.effects import WorkerContext
from julep.execution.serve import (
    DEFAULT_TASK_QUEUE,
    HealthServer,
    WorkerServeSettings,
    _versioning_worker_kwargs,
    load_application_runtime,
    load_context_factory,
    serve,
    smoke_test_worker,
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
    assert s.application is None
    assert s.runtime_declarations_hash is None
    assert s.address == "localhost:7233"
    assert s.namespace == "default"
    assert s.task_queue == DEFAULT_TASK_QUEUE == "julep"
    assert s.api_key is None and s.tls is False
    assert s.graceful_shutdown_s == 30.0
    assert s.max_concurrent_activities is None
    assert s.max_concurrent_workflow_tasks is None
    assert s.health_port is None
    assert s.build_id is None
    assert s.use_worker_versioning is False


def test_worker_settings_preserve_original_positional_field_order():
    settings = WorkerServeSettings(
        "m:f",
        "temporal.internal:7233",
        "production",
        "summary-lane",
    )

    assert settings.address == "temporal.internal:7233"
    assert settings.namespace == "production"
    assert settings.task_queue == "summary-lane"
    assert settings.application is None
    assert settings.runtime_declarations_hash is None


def test_smoke_test_waits_for_ready_then_drains(monkeypatch):
    calls: list[str] = []

    async def fake_serve(
        settings,
        *,
        shutdown_event,
        ready_event,
        verify_connection,
    ):
        assert settings.health_port is None
        assert verify_connection is True
        calls.append("started")
        ready_event.set()
        await shutdown_event.wait()
        calls.append("drained")

    serve_module = import_module("julep.execution.serve")
    monkeypatch.setattr(serve_module, "serve", fake_serve)

    run(
        smoke_test_worker(
            WorkerServeSettings(context_factory="m:f", health_port=8080),
            poll_seconds=0.001,
        )
    )

    assert calls == ["started", "drained"]


def test_from_env_full_parse():
    runtime_hash = "sha256:" + "a" * 64
    s = WorkerServeSettings.from_env({
        "WORKER_CONTEXT_FACTORY": "pkg.mod:make",
        "WORKER_APPLICATION": "pkg.application:application",
        "WORKER_RUNTIME_DECLARATIONS_HASH": runtime_hash,
        "TEMPORAL_ADDRESS": "temporal-frontend.temporal.svc:7233",
        "TEMPORAL_NAMESPACE": "prod",
        "TEMPORAL_TASK_QUEUE": "lane-embeddings",
        "WORKER_GRACEFUL_SHUTDOWN_S": "12.5",
        "WORKER_MAX_CONCURRENT_ACTIVITIES": "16",
        "WORKER_MAX_CONCURRENT_WORKFLOW_TASKS": "8",
        "WORKER_HEALTH_PORT": "8080",
    })
    assert s.address == "temporal-frontend.temporal.svc:7233"
    assert s.application == "pkg.application:application"
    assert s.runtime_declarations_hash == runtime_hash
    assert s.namespace == "prod"
    assert s.task_queue == "lane-embeddings"
    assert s.graceful_shutdown_s == 12.5
    assert s.max_concurrent_activities == 16
    assert s.max_concurrent_workflow_tasks == 8
    assert s.health_port == 8080


def test_from_env_parses_versioning():
    s = WorkerServeSettings.from_env({
        "WORKER_CONTEXT_FACTORY": "m:f",
        "JULEP_WORKER_BUILD_ID": "build-42",
        "JULEP_WORKER_VERSIONING": "1",
    })
    assert s.build_id == "build-42"
    assert s.use_worker_versioning is True


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
    with pytest.raises(ValueError, match="must be set together"):
        WorkerServeSettings.from_env({**base, "WORKER_APPLICATION": "pkg:application"})
    with pytest.raises(ValueError, match="sha256"):
        WorkerServeSettings.from_env(
            {
                **base,
                "WORKER_APPLICATION": "pkg:application",
                "WORKER_RUNTIME_DECLARATIONS_HASH": "latest",
            }
        )


def test_required_payload_encryption_rejects_missing_keys():
    with pytest.raises(ValueError, match="payload encryption is required"):
        WorkerServeSettings.from_env(
            {
                "WORKER_CONTEXT_FACTORY": "m:f",
                "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "true",
            }
        )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporal extra not installed")
def test_run_worker_required_payload_encryption_rejects_missing_keys(
    monkeypatch,
):
    from julep.execution.worker import run_worker

    monkeypatch.setenv("TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED", "true")
    monkeypatch.delenv("TEMPORAL_PAYLOAD_KEYS", raising=False)
    monkeypatch.delenv("TEMPORAL_PAYLOAD_KEY_ID", raising=False)

    with pytest.raises(ValueError, match="payload encryption is required"):
        run(run_worker())


def test_from_env_versioning_bad_bool():
    with pytest.raises(ValueError, match="JULEP_WORKER_VERSIONING"):
        WorkerServeSettings.from_env({
            "WORKER_CONTEXT_FACTORY": "m:f",
            "JULEP_WORKER_VERSIONING": "banana",
        })


def test_versioning_kwargs_unset_is_empty():
    settings = WorkerServeSettings(context_factory="m:f")
    assert _versioning_worker_kwargs(settings) == {}


def test_versioning_kwargs_defaults_build_id_to_package_version():
    settings = WorkerServeSettings(context_factory="m:f", use_worker_versioning=True)
    assert _versioning_worker_kwargs(settings) == {
        "build_id": __version__,
        "use_worker_versioning": True,
    }


def test_versioning_kwargs_missing_metadata_raises(monkeypatch):
    from importlib import import_module

    serve_mod = import_module("julep.execution.serve")

    def _boom(_name):
        raise serve_mod.PackageNotFoundError(_name)

    monkeypatch.setattr(serve_mod, "version", _boom)
    settings = WorkerServeSettings(context_factory="m:f", use_worker_versioning=True)
    with pytest.raises(JulepError, match="JULEP_WORKER_BUILD_ID"):
        _versioning_worker_kwargs(settings)


def test_versioning_kwargs_explicit_build_id_survives_missing_metadata(monkeypatch):
    from importlib import import_module

    serve_mod = import_module("julep.execution.serve")

    def _boom(_name):
        raise serve_mod.PackageNotFoundError(_name)

    monkeypatch.setattr(serve_mod, "version", _boom)
    settings = WorkerServeSettings(
        context_factory="m:f", build_id="v9", use_worker_versioning=True
    )
    assert _versioning_worker_kwargs(settings) == {
        "build_id": "v9",
        "use_worker_versioning": True,
    }


def test_versioning_kwargs_explicit_build_id():
    settings = WorkerServeSettings(
        context_factory="m:f",
        build_id="v9",
        use_worker_versioning=True,
    )
    assert _versioning_worker_kwargs(settings) == {
        "build_id": "v9",
        "use_worker_versioning": True,
    }


def test_versioning_kwargs_build_id_without_versioning():
    settings = WorkerServeSettings(
        context_factory="m:f",
        build_id="v9",
        use_worker_versioning=False,
    )
    assert _versioning_worker_kwargs(settings) == {"build_id": "v9"}


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


def test_load_application_runtime_registers_release_pinned_reasoner(
    monkeypatch,
):
    from julep.registry import DEFAULT_REGISTRY, Registry

    reasoner_name = "serve-application-runtime"
    application = Application(
        "memory",
        [
            PipelineSpec(
                "summary",
                think(reasoner_name),
                reasoners=(Reasoner(reasoner_name, "test:model"),),
            )
        ],
    )
    module_name = "_julep_test_worker_application"
    module = types.ModuleType(module_name)
    module.application = application
    monkeypatch.setitem(sys.modules, module_name, module)
    context_registry = Registry()
    existing = DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
    try:
        load_application_runtime(
            f"{module_name}:application",
            expected_hash=application.runtime_declarations_hash,
            registry=context_registry,
        )

        assert DEFAULT_REGISTRY.get_reasoner(reasoner_name).model == "test:model"
        assert context_registry.get_reasoner(reasoner_name).model == "test:model"
    finally:
        DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
        if existing is not None:
            DEFAULT_REGISTRY.reasoners[reasoner_name] = existing


def test_load_application_runtime_restores_string_declared_reasoner(
    monkeypatch,
):
    from julep.registry import DEFAULT_REGISTRY, Registry

    reasoner_name = "serve-application-string-runtime"
    reasoner = Reasoner(reasoner_name, "test:model")
    existing = DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
    try:
        DEFAULT_REGISTRY.register_reasoner(reasoner)
        application = Application(
            "memory",
            [
                PipelineSpec(
                    "summary",
                    think(reasoner_name),
                    reasoners=(reasoner_name,),
                )
            ],
        )
        expected_hash = application.runtime_declarations_hash
        module_name = "_julep_test_worker_string_application"
        module = types.ModuleType(module_name)
        module.application = application
        monkeypatch.setitem(sys.modules, module_name, module)

        context_registry = Registry()
        context_registry.register_reasoner(reasoner)
        DEFAULT_REGISTRY.reasoners.pop(reasoner_name)

        load_application_runtime(
            f"{module_name}:application",
            expected_hash=expected_hash,
            registry=context_registry,
        )

        assert DEFAULT_REGISTRY.get_reasoner(reasoner_name) == reasoner
        assert context_registry.get_reasoner(reasoner_name) == reasoner
    finally:
        DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
        if existing is not None:
            DEFAULT_REGISTRY.reasoners[reasoner_name] = existing


def test_load_application_runtime_rejects_missing_renderer(monkeypatch):
    from julep.registry import DEFAULT_REGISTRY

    reasoner_name = "serve-application-missing-renderer"
    renderer_name = "serve-renderer-does-not-exist"
    application = Application(
        "memory",
        [
            PipelineSpec(
                "summary",
                think(reasoner_name),
                reasoners=(
                    Reasoner(
                        reasoner_name,
                        "test:model",
                        system_render=renderer_name,
                    ),
                ),
            )
        ],
    )
    module_name = "_julep_test_worker_missing_renderer_application"
    module = types.ModuleType(module_name)
    module.application = application
    monkeypatch.setitem(sys.modules, module_name, module)
    existing_reasoner = DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
    existing_renderer = DEFAULT_REGISTRY.renderers.pop(renderer_name, None)
    try:
        with pytest.raises(ApplicationDefinitionError, match="unknown renderer"):
            load_application_runtime(
                f"{module_name}:application",
                expected_hash="sha256:" + "0" * 64,
            )
    finally:
        DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
        if existing_reasoner is not None:
            DEFAULT_REGISTRY.reasoners[reasoner_name] = existing_reasoner
        if existing_renderer is not None:
            DEFAULT_REGISTRY.renderers[renderer_name] = existing_renderer


def test_serve_rejects_factory_returning_wrong_type():
    settings = WorkerServeSettings(context_factory=f"{__name__}:not_a_factory")
    if not HAVE_TEMPORAL:
        with pytest.raises(JulepError, match="temporal"):
            run(serve(settings))
        return
    with pytest.raises(JulepError, match="must return a WorkerContext"):
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


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_build_worker_forwards_versioning_kwargs(monkeypatch):
    from julep.execution import worker as worker_mod
    from julep.execution.worker import build_worker

    captured: dict[str, Any] = {}

    class FakeWorker:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            captured["args"] = args
            captured["kwargs"] = kwargs

    async def _noop_mcp(server, tool, value, idempotency_key, principal=None):
        return value

    monkeypatch.delenv("STORE_URL", raising=False)
    monkeypatch.setattr(worker_mod, "Worker", FakeWorker)
    with warnings.catch_warnings():
        # The JULEP_WORKER_* seam intentionally maps to Temporal's deprecated
        # Worker kwargs for now; suppress future runtime warnings around this call.
        warnings.simplefilter("ignore", DeprecationWarning)
        build_worker(
            object(),
            WorkerContext(mcp_call=_noop_mcp),
            build_id="test-bid",
            use_worker_versioning=True,
        )

    assert captured["kwargs"]["build_id"] == "test-bid"
    assert captured["kwargs"]["use_worker_versioning"] is True


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_serve_forwards_versioning_kwargs_to_build_worker(monkeypatch):
    import julep.execution.worker as worker_mod
    from temporalio.client import Client

    captured: dict[str, Any] = {}

    class FakeWorker:
        def __init__(self) -> None:
            self._stop = asyncio.Event()

        async def run(self) -> None:
            await self._stop.wait()

        async def shutdown(self) -> None:
            self._stop.set()

    def fake_build_worker(client, context, *, task_queue, **kwargs):
        captured["task_queue"] = task_queue
        captured["kwargs"] = kwargs
        return FakeWorker()

    async def fake_connect(target, **kwargs):
        return object()

    monkeypatch.setattr(worker_mod, "build_worker", fake_build_worker)
    monkeypatch.setattr(Client, "connect", staticmethod(fake_connect))

    settings = WorkerServeSettings(
        context_factory=f"{__name__}:make_context",
        build_id="serve-bid",
        use_worker_versioning=True,
    )

    async def _drive() -> None:
        stop = asyncio.Event()
        task = asyncio.create_task(serve(settings, shutdown_event=stop))
        try:
            for _ in range(1000):
                if "kwargs" in captured:
                    break
                await asyncio.sleep(0.005)
            assert "kwargs" in captured, "serve() never called build_worker"
        finally:
            stop.set()
            await asyncio.wait_for(task, timeout=10)

    run(_drive())

    assert captured["kwargs"]["build_id"] == "serve-bid"
    assert captured["kwargs"]["use_worker_versioning"] is True


# --------------------------------------------------------------------------- #
# Lifecycle against the time-skipping server: poll, execute, drain on shutdown.
# --------------------------------------------------------------------------- #
async def _serve_lifecycle():
    from temporalio.testing import WorkflowEnvironment

    from julep import call, freeze, manifest_to_json, mcp
    from julep.contracts import McpAnnotations
    from julep.execution.harness import run_flow
    from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec

    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    snapshot = McpSnapshot(servers={"srv": McpServerSnapshot(server="srv", version="1", tools={
        "inc": McpToolSpec(input_schema={}, annotations=ann),
    })})
    fr = freeze(call(mcp("srv", "inc")), snapshot)

    async with await WorkflowEnvironment.start_time_skipping() as env:
        settings = WorkerServeSettings(
            context_factory=f"{__name__}:make_context",
            address=env.client.service_client.config.target_host,
            task_queue="julep-serve",
            graceful_shutdown_s=5.0,
        )
        stop = asyncio.Event()
        serve_task = asyncio.create_task(serve(settings, shutdown_event=stop))
        try:
            out = await run_flow(
                env.client, fr.flow.to_json(), manifest_to_json(fr.manifest),
                session_id="serve-1", input=2, task_queue="julep-serve",
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
    with pytest.raises(JulepError, match="julep\\[temporal\\]"):
        run(serve(settings))
