"""Container-ready worker entrypoint (k8s / KEDA host shell).

This is the host shell around :func:`julep.execution.worker.build_worker`
for running workers as horizontally scaled container replicas — typically a
Kubernetes Deployment autoscaled by KEDA's ``temporal`` scaler on task-queue
backlog (see docs/deploy-kubernetes.md). The framework pieces it adds:

* :class:`WorkerServeSettings` — connection/tuning knobs read from the
  environment (:meth:`WorkerServeSettings.from_env`), the natural surface for a
  container. Application releases name their explicit ``Application`` object
  and its immutable declarations hash so inline reasoners are registered before
  polling. The one thing that cannot come from an env var is the
  :class:`~julep.execution.effects.WorkerContext` (it holds live
  callables), so it is named by ``WORKER_CONTEXT_FACTORY`` as an importable
  ``module:attr`` factory — required, never defaulted.
* :class:`HealthServer` — a stdlib HTTP listener for kubelet probes:
  ``/healthz`` (liveness: the event loop is responsive) and ``/readyz``
  (readiness: polling; flips to 503 the moment a drain starts).
* :func:`serve` — run the worker until SIGTERM/SIGINT, then drain: stop
  polling, let in-flight activities finish within the graceful window, exit 0.
  Replicas scaled in by KEDA therefore finish their work instead of dropping it.

Module import is stdlib-only so settings parsing and health probes are testable
without Temporal; :func:`serve` itself requires the ``temporal`` extra and says
so explicitly when it is missing.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import os
import re
import signal
import sys
from dataclasses import dataclass, field, replace
from datetime import timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional

from .. import _env
from .._specload import resolve_spec
from ..errors import JulepError
from ..trajectory import RedactionConfig, build_redactor
from .effects import WorkerContext

if sys.version_info >= (3, 11):
    import tomllib as _tomllib
else:
    _tomllib = None

if TYPE_CHECKING:
    from ..registry import Registry

# Canonical default task queue. `execution.worker` re-exports this; it is
# defined here because this module must import without temporalio.
DEFAULT_TASK_QUEUE = "julep"

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def read_redaction_pyproject(root: Path) -> Optional[dict[str, Any]]:
    """Read ``[tool.julep.redaction]`` without coupling to the authoring CLI."""
    if _tomllib is None:
        return None
    try:
        with (root / "pyproject.toml").open("rb") as handle:
            data = _tomllib.load(handle)
    except (OSError, ValueError):
        return None
    tool = data.get("tool")
    if not isinstance(tool, dict):
        return None
    julep = tool.get("julep")
    if not isinstance(julep, dict):
        return None
    redaction = julep.get("redaction")
    if not isinstance(redaction, dict):
        return None
    return dict(redaction)


def _env_bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None or raw == "":
        return default
    lowered = raw.strip().lower()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise ValueError(f"{name} must be a boolean (true/false), got {raw!r}")


def _env_int(env: Mapping[str, str], name: str) -> Optional[int]:
    raw = env.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _env_float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = env.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


def payload_encryption_from_env(
    env: Mapping[str, str],
) -> tuple[Optional[str], Optional[str], bool]:
    """Parse the shared Temporal payload-encryption environment contract.

    Every client and worker entrypoint uses this helper so an explicit
    ``TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED=true`` can never silently fall back
    to Temporal's plaintext data converter.
    """

    payload_keys = env.get("TEMPORAL_PAYLOAD_KEYS") or None
    payload_key_id = env.get("TEMPORAL_PAYLOAD_KEY_ID") or None
    if (payload_keys is None) != (payload_key_id is None):
        raise ValueError(
            "TEMPORAL_PAYLOAD_KEYS and TEMPORAL_PAYLOAD_KEY_ID must be set together"
        )
    required = _env_bool(
        env,
        "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED",
        default=False,
    )
    if required and payload_keys is None:
        raise ValueError(
            "Temporal payload encryption is required but "
            "TEMPORAL_PAYLOAD_KEYS and TEMPORAL_PAYLOAD_KEY_ID are missing"
        )
    return payload_keys, payload_key_id, required


@dataclass(frozen=True)
class WorkerServeSettings:
    """Environment-shaped configuration for one worker replica.

    ``context_factory`` is a ``module:attr`` spec naming a zero-argument
    callable (sync or async) that returns the process's
    :class:`~julep.execution.effects.WorkerContext`. ``application`` names the
    release-pinned :class:`~julep.app.Application` whose inline declarations
    are verified and registered into its context before polling. ``tls``
    defaults to True exactly when ``api_key`` is set (Temporal Cloud);
    self-hosted plaintext stays the default otherwise.
    """

    context_factory: str
    address: str = "localhost:7233"
    namespace: str = "default"
    task_queue: str = DEFAULT_TASK_QUEUE
    api_key: Optional[str] = None
    tls: bool = False
    graceful_shutdown_s: float = 30.0
    max_concurrent_activities: Optional[int] = None
    max_concurrent_workflow_tasks: Optional[int] = None
    health_port: Optional[int] = None
    build_id: Optional[str] = None
    use_worker_versioning: bool = False
    payload_keys: Optional[str] = field(default=None, repr=False)
    payload_key_id: Optional[str] = None
    payload_encryption_required: bool = False
    application: Optional[str] = None
    runtime_declarations_hash: Optional[str] = None
    redaction: Optional[RedactionConfig] = None
    materialized_secret_environment: dict[str, str] = field(
        default_factory=dict, repr=False
    )
    blob_store_url: Optional[str] = None

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "WorkerServeSettings":
        """Read settings from ``env`` (default ``os.environ``).

        Variables: ``WORKER_CONTEXT_FACTORY`` (required), ``WORKER_APPLICATION``
        and ``WORKER_RUNTIME_DECLARATIONS_HASH`` (paired), ``TEMPORAL_ADDRESS``,
        ``TEMPORAL_NAMESPACE``, ``TEMPORAL_TASK_QUEUE``, ``TEMPORAL_API_KEY``,
        ``TEMPORAL_TLS``, ``WORKER_GRACEFUL_SHUTDOWN_S``,
        ``WORKER_MAX_CONCURRENT_ACTIVITIES``,
        ``WORKER_MAX_CONCURRENT_WORKFLOW_TASKS``, ``WORKER_HEALTH_PORT``,
        ``JULEP_WORKER_BUILD_ID``, ``JULEP_WORKER_VERSIONING``, ``JULEP_REDACTION``,
        and ``JULEP_BLOB_STORE_URL``.
        """
        e: Mapping[str, str] = os.environ if env is None else env
        factory = e.get("WORKER_CONTEXT_FACTORY")
        if not factory:
            raise ValueError(
                "WORKER_CONTEXT_FACTORY is required: set it to a 'module:attr' factory "
                "returning a WorkerContext. A worker without explicit context wiring "
                "would silently run with no tool or LLM callers, so there is no default."
            )
        application = e.get("WORKER_APPLICATION") or None
        runtime_declarations_hash = (
            e.get("WORKER_RUNTIME_DECLARATIONS_HASH") or None
        )
        if (application is None) != (runtime_declarations_hash is None):
            raise ValueError(
                "WORKER_APPLICATION and WORKER_RUNTIME_DECLARATIONS_HASH "
                "must be set together"
            )
        if (
            runtime_declarations_hash is not None
            and re.fullmatch(r"sha256:[0-9a-f]{64}", runtime_declarations_hash) is None
        ):
            raise ValueError(
                "WORKER_RUNTIME_DECLARATIONS_HASH must be "
                "sha256:<64 lowercase hex>"
            )
        from ..secrets import SecretResolver, materialize_secret_environment

        secret_resolver = SecretResolver.from_env(e)
        materialized_secret_environment = materialize_secret_environment(
            e, resolver=secret_resolver
        )
        raw_api_key = e.get("TEMPORAL_API_KEY") or None
        api_key = (
            None if raw_api_key is None else secret_resolver.resolve_ref(raw_api_key)
        )
        redaction_json = e.get("JULEP_REDACTION", "").strip()
        redaction = (
            RedactionConfig.from_json(redaction_json) if redaction_json else None
        )
        payload_environment = dict(e)
        if payload_environment.get("TEMPORAL_PAYLOAD_KEYS"):
            payload_environment["TEMPORAL_PAYLOAD_KEYS"] = secret_resolver.resolve_ref(
                payload_environment["TEMPORAL_PAYLOAD_KEYS"]
            )
        (
            payload_keys,
            payload_key_id,
            payload_encryption_required,
        ) = payload_encryption_from_env(payload_environment)
        return cls(
            context_factory=factory,
            application=application,
            runtime_declarations_hash=runtime_declarations_hash,
            address=e.get("TEMPORAL_ADDRESS", "localhost:7233"),
            namespace=e.get("TEMPORAL_NAMESPACE", "default"),
            task_queue=e.get("TEMPORAL_TASK_QUEUE", DEFAULT_TASK_QUEUE),
            api_key=api_key,
            tls=_env_bool(e, "TEMPORAL_TLS", default=api_key is not None),
            graceful_shutdown_s=_env_float(e, "WORKER_GRACEFUL_SHUTDOWN_S", 30.0),
            max_concurrent_activities=_env_int(e, "WORKER_MAX_CONCURRENT_ACTIVITIES"),
            max_concurrent_workflow_tasks=_env_int(e, "WORKER_MAX_CONCURRENT_WORKFLOW_TASKS"),
            health_port=_env_int(e, "WORKER_HEALTH_PORT"),
            build_id=_env.get(_env.JULEP_WORKER_BUILD_ID, environ=e) or None,
            use_worker_versioning=_env_bool(
                e,
                _env.JULEP_WORKER_VERSIONING,
                default=False,
            ),
            payload_keys=payload_keys,
            payload_key_id=payload_key_id,
            payload_encryption_required=payload_encryption_required,
            redaction=redaction,
            materialized_secret_environment=materialized_secret_environment,
            blob_store_url=(e.get(_env.JULEP_BLOB_STORE_URL) or None),
        )


def _versioning_worker_kwargs(settings: WorkerServeSettings) -> dict[str, Any]:
    """Assemble the opt-in Build-ID / worker-versioning kwargs for build_worker.

    DELIBERATE deprecated-kwarg use: temporalio 1.30 deprecates `build_id` /
    `use_worker_versioning` on Worker in favor of `deployment_config`. The stable
    contract we ship is the JULEP_WORKER_* env seam (parsed into WorkerServeSettings);
    the Worker kwarg can migrate to deployment_config later without touching that seam.
    Omit-when-unset: versioning off + no build_id -> {} so build_worker is called
    byte-identically to before this task. When versioning is on and no explicit
    build_id was given, we default it to the installed package version; if that
    version cannot be resolved (source checkout / metadata-less image) we FAIL LOUDLY
    rather than advertise a constant fake Build ID across incompatible worker images
    (that silent fallback would defeat the versioning safety this feature provides — G-8).
    """
    kwargs: dict[str, Any] = {}
    build_id = settings.build_id
    if settings.use_worker_versioning and build_id is None:
        try:
            build_id = version("julep")
        except PackageNotFoundError as exc:
            raise JulepError(
                "worker versioning is on (JULEP_WORKER_VERSIONING=1) but no "
                "JULEP_WORKER_BUILD_ID is set and the julep version cannot "
                "be read from installed package metadata (source checkout or an image "
                "without distribution metadata). Set JULEP_WORKER_BUILD_ID to a stable, "
                "per-image Build ID: versioning must never advertise a constant fake "
                "Build ID across mutually-incompatible worker images."
            ) from exc
    if build_id is not None:
        kwargs["build_id"] = build_id
    if settings.use_worker_versioning:
        kwargs["use_worker_versioning"] = True
    return kwargs


def load_context_factory(spec: str) -> Callable[[], Any]:
    """Resolve a ``module:attr`` spec to the context factory callable.

    ``attr`` may be dotted (``module:obj.method``). Raises :class:`ValueError`
    with the failing spec on any bad shape, missing module, missing attribute,
    or non-callable target — the CLI surfaces these as one-line errors.
    """
    return resolve_spec(spec, what="context factory")


class HealthServer:
    """Minimal stdlib HTTP listener for kubelet probes.

    ``GET /healthz`` always answers 200 while the event loop is alive
    (liveness). ``GET /readyz`` answers 200 when :attr:`ready` is True and 503
    otherwise (readiness/drain). Anything else is 404. One-shot connections,
    no keep-alive — exactly what probes send.
    """

    def __init__(self, port: int, *, host: str = "0.0.0.0") -> None:
        self._host = host
        self._port = port
        self._server: Optional[asyncio.AbstractServer] = None
        self.ready = False

    @property
    def port(self) -> int:
        """The bound port (useful when constructed with port 0)."""
        if self._server is None or not self._server.sockets:
            raise RuntimeError("health server is not running")
        return int(self._server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, self._host, self._port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            request_line = await reader.readline()
            while True:  # drain headers; probes send no body
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
            parts = request_line.decode("latin-1", "replace").split()
            path = parts[1] if len(parts) >= 2 else ""
            if path == "/healthz":
                status, body = "200 OK", b"ok"
            elif path == "/readyz":
                if self.ready:
                    status, body = "200 OK", b"ready"
                else:
                    status, body = "503 Service Unavailable", b"not ready"
            else:
                status, body = "404 Not Found", b"not found"
            head = (
                f"HTTP/1.1 {status}\r\nContent-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
            )
            writer.write(head.encode("latin-1") + body)
            await writer.drain()
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()


async def _resolve_context(spec: str) -> WorkerContext:
    factory = load_context_factory(spec)
    context = factory()
    if inspect.isawaitable(context):
        context = await context
    if not isinstance(context, WorkerContext):
        raise JulepError(
            f"context factory {spec!r} must return a WorkerContext, "
            f"got {type(context).__name__}"
        )
    return context


def _install_default_redactor(
    context: WorkerContext, settings: WorkerServeSettings
) -> None:
    # The dynamic operator scrubber remains live after worker startup: secrets
    # first resolved by a later MCP call are covered without replacing context.
    from ..secrets import operator_secret_redactor
    from ..trajectory import redact_secret_shaped

    base = context.redactor
    if base is None:
        base = (
            build_redactor(settings.redaction)
            if settings.redaction is not None
            else redact_secret_shaped
        )
    context.redactor = operator_secret_redactor(base)


def _install_blob_store(
    context: WorkerContext, settings: WorkerServeSettings
) -> None:
    """Install the operator-configured store before worker construction.

    A factory store and URL together are ambiguous: changing the backend makes
    retained transcript refs unreadable, so startup fails instead of choosing
    one silently.
    """

    from .blobstore import _resolve_blob_store_configuration

    context.blob_store = _resolve_blob_store_configuration(
        context.blob_store,
        settings.blob_store_url,
        explicit_source="WORKER_CONTEXT_FACTORY",
    )


def load_application_runtime(
    spec: str,
    *,
    expected_hash: str,
    registry: Optional[Registry] = None,
) -> None:
    """Load and verify release-pinned application declarations for a worker."""

    from ..app import load_application_spec

    application = load_application_spec(spec)
    application.register_runtime_declarations(
        expected_hash=expected_hash,
        registry=registry,
    )


async def serve(
    settings: WorkerServeSettings,
    *,
    shutdown_event: Optional[asyncio.Event] = None,
    ready_event: Optional[asyncio.Event] = None,
    verify_connection: bool = False,
) -> None:
    """Run one worker replica until shutdown, then drain gracefully.

    Lifecycle: start the health listener (liveness goes green first, so a slow
    Temporal connect cannot get the pod killed by a liveness probe), resolve the
    context factory, connect, build the worker, start polling, flip readiness.
    On SIGTERM/SIGINT (or ``shutdown_event``, the test seam): flip readiness to
    503, stop polling, let in-flight activities finish within
    ``graceful_shutdown_s``, and return. A worker crash propagates loudly —
    the replica exits non-zero and the orchestrator restarts it (no silent
    degraded mode).
    """
    try:
        from temporalio.client import Client
    except ImportError as exc:
        raise JulepError(
            "serve() requires temporalio; install 'julep[temporal]'"
        ) from exc
    from .worker import build_worker, encrypted_payload_converter

    health: Optional[HealthServer] = None
    if settings.health_port is not None:
        health = HealthServer(settings.health_port)
        await health.start()

    stop = shutdown_event if shutdown_event is not None else asyncio.Event()
    loop = asyncio.get_running_loop()
    installed: list[signal.Signals] = []
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
            installed.append(sig)
        except (NotImplementedError, RuntimeError):
            pass  # non-main thread or platform without loop signal handlers

    try:
        # Application-specific worker env is a startup-time injection surface.
        # Values remain pinned until this process restarts.
        os.environ.update(settings.materialized_secret_environment)
        context = await _resolve_context(settings.context_factory)
        _install_blob_store(context, settings)
        from .blobstore import _initialize_blob_store

        await _initialize_blob_store(context.blob_store)
        _install_default_redactor(context, settings)
        if settings.application is not None:
            if settings.runtime_declarations_hash is None:
                raise JulepError(
                    "worker application requires a runtime declarations hash"
                )
            load_application_runtime(
                settings.application,
                expected_hash=settings.runtime_declarations_hash,
                registry=context.registry,
            )

        connect_kwargs: dict[str, Any] = {
            "namespace": settings.namespace,
            # Always pass tls explicitly: the SDK auto-enables TLS whenever
            # api_key is set and tls is left unset, which would silently
            # override an explicit TEMPORAL_TLS=false.
            "tls": settings.tls,
        }
        if settings.api_key is not None:
            connect_kwargs["api_key"] = settings.api_key
        if settings.payload_keys is not None:
            from .codec import parse_aes_gcm_keyring
            from .trace_headers import WorkflowTraceHeadersInterceptor
            from temporalio.common import HeaderCodecBehavior

            assert settings.payload_key_id is not None
            connect_kwargs["data_converter"] = encrypted_payload_converter(
                parse_aes_gcm_keyring(settings.payload_keys),
                active_key_id=settings.payload_key_id,
            )
            connect_kwargs["header_codec_behavior"] = HeaderCodecBehavior.CODEC
            connect_kwargs["interceptors"] = [WorkflowTraceHeadersInterceptor()]
        client = await Client.connect(settings.address, **connect_kwargs)
        if verify_connection:
            healthy = await client.service_client.check_health(
                timeout=timedelta(seconds=10)
            )
            if not healthy:
                raise JulepError("Temporal frontend health check failed")

        worker_kwargs: dict[str, Any] = {
            "graceful_shutdown_timeout": timedelta(seconds=settings.graceful_shutdown_s),
        }
        if settings.max_concurrent_activities is not None:
            worker_kwargs["max_concurrent_activities"] = settings.max_concurrent_activities
        if settings.max_concurrent_workflow_tasks is not None:
            worker_kwargs["max_concurrent_workflow_tasks"] = (
                settings.max_concurrent_workflow_tasks
            )
        worker_kwargs.update(_versioning_worker_kwargs(settings))
        worker = build_worker(
            client, context, task_queue=settings.task_queue, **worker_kwargs
        )

        run_task = asyncio.create_task(worker.run())
        stop_task = asyncio.create_task(stop.wait())
        if health is not None:
            health.ready = True
        if ready_event is not None:
            ready_event.set()
        try:
            await asyncio.wait({run_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
            if health is not None:
                health.ready = False
            if run_task.done():
                await run_task  # propagate a worker failure, never swallow it
            else:
                await worker.shutdown()  # stop polling; drain within the grace window
                await run_task
        finally:
            stop_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await stop_task
    finally:
        for sig in installed:
            loop.remove_signal_handler(sig)
        if health is not None:
            await health.stop()


async def smoke_test_worker(
    settings: WorkerServeSettings,
    *,
    poll_seconds: float = 3.0,
    startup_timeout_seconds: float = 30.0,
) -> None:
    """Start the real worker briefly, then drain it after polling is established."""

    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")
    if startup_timeout_seconds <= 0:
        raise ValueError("startup_timeout_seconds must be positive")

    stop = asyncio.Event()
    ready = asyncio.Event()
    task = asyncio.create_task(
        serve(
            replace(settings, health_port=None),
            shutdown_event=stop,
            ready_event=ready,
            verify_connection=True,
        )
    )
    ready_task = asyncio.create_task(ready.wait())
    try:
        done, _pending = await asyncio.wait(
            {task, ready_task},
            timeout=startup_timeout_seconds,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if task in done:
            await task
            raise JulepError("worker exited before becoming ready for its smoke test")
        if ready_task not in done:
            raise TimeoutError(
                "worker did not become ready before the smoke-test startup timeout"
            )
        await asyncio.sleep(poll_seconds)
        if task.done():
            await task
            raise JulepError("worker exited before completing the smoke-test window")
        stop.set()
        await asyncio.wait_for(
            task,
            timeout=max(5.0, settings.graceful_shutdown_s + 5.0),
        )
    finally:
        ready_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ready_task
        if not task.done():
            stop.set()
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


__all__ = [
    "DEFAULT_TASK_QUEUE",
    "HealthServer",
    "WorkerServeSettings",
    "load_application_runtime",
    "load_context_factory",
    "payload_encryption_from_env",
    "serve",
    "smoke_test_worker",
]
