"""Container-ready worker entrypoint (k8s / KEDA host shell).

This is the host shell around :func:`composable_agents.execution.worker.build_worker`
for running workers as horizontally scaled container replicas — typically a
Kubernetes Deployment autoscaled by KEDA's ``temporal`` scaler on task-queue
backlog (see docs/deploy-kubernetes.md). The framework pieces it adds:

* :class:`WorkerServeSettings` — connection/tuning knobs read from the
  environment (:meth:`WorkerServeSettings.from_env`), the natural surface for a
  container. The one thing that cannot come from an env var is the
  :class:`~composable_agents.execution.effects.WorkerContext` (it holds live
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
import signal
from dataclasses import dataclass
from datetime import timedelta
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable, Mapping, Optional

from ..errors import ComposableAgentsError
from .effects import WorkerContext

# Canonical default task queue. `execution.worker` re-exports this; it is
# defined here because this module must import without temporalio.
DEFAULT_TASK_QUEUE = "composable-agents"

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


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


@dataclass(frozen=True)
class WorkerServeSettings:
    """Environment-shaped configuration for one worker replica.

    ``context_factory`` is a ``module:attr`` spec naming a zero-argument
    callable (sync or async) that returns the process's
    :class:`~composable_agents.execution.effects.WorkerContext`. ``tls``
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

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "WorkerServeSettings":
        """Read settings from ``env`` (default ``os.environ``).

        Variables: ``WORKER_CONTEXT_FACTORY`` (required), ``TEMPORAL_ADDRESS``,
        ``TEMPORAL_NAMESPACE``, ``TEMPORAL_TASK_QUEUE``, ``TEMPORAL_API_KEY``,
        ``TEMPORAL_TLS``, ``WORKER_GRACEFUL_SHUTDOWN_S``,
        ``WORKER_MAX_CONCURRENT_ACTIVITIES``,
        ``WORKER_MAX_CONCURRENT_WORKFLOW_TASKS``, ``WORKER_HEALTH_PORT``,
        ``CA_WORKER_BUILD_ID``, ``CA_WORKER_VERSIONING``.
        """
        e: Mapping[str, str] = os.environ if env is None else env
        factory = e.get("WORKER_CONTEXT_FACTORY")
        if not factory:
            raise ValueError(
                "WORKER_CONTEXT_FACTORY is required: set it to a 'module:attr' factory "
                "returning a WorkerContext. A worker without explicit context wiring "
                "would silently run with no tool or LLM callers, so there is no default."
            )
        api_key = e.get("TEMPORAL_API_KEY") or None
        return cls(
            context_factory=factory,
            address=e.get("TEMPORAL_ADDRESS", "localhost:7233"),
            namespace=e.get("TEMPORAL_NAMESPACE", "default"),
            task_queue=e.get("TEMPORAL_TASK_QUEUE", DEFAULT_TASK_QUEUE),
            api_key=api_key,
            tls=_env_bool(e, "TEMPORAL_TLS", default=api_key is not None),
            graceful_shutdown_s=_env_float(e, "WORKER_GRACEFUL_SHUTDOWN_S", 30.0),
            max_concurrent_activities=_env_int(e, "WORKER_MAX_CONCURRENT_ACTIVITIES"),
            max_concurrent_workflow_tasks=_env_int(e, "WORKER_MAX_CONCURRENT_WORKFLOW_TASKS"),
            health_port=_env_int(e, "WORKER_HEALTH_PORT"),
            build_id=e.get("CA_WORKER_BUILD_ID") or None,
            use_worker_versioning=_env_bool(e, "CA_WORKER_VERSIONING", default=False),
        )


def _versioning_worker_kwargs(settings: WorkerServeSettings) -> dict[str, Any]:
    """Assemble the opt-in Build-ID / worker-versioning kwargs for build_worker.

    DELIBERATE deprecated-kwarg use: temporalio 1.30 deprecates `build_id` /
    `use_worker_versioning` on Worker in favor of `deployment_config`. The stable
    contract we ship is the CA_WORKER_* env seam (parsed into WorkerServeSettings);
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
            build_id = version("composable-agents")
        except PackageNotFoundError as exc:
            raise ComposableAgentsError(
                "worker versioning is on (CA_WORKER_VERSIONING=1) but no "
                "CA_WORKER_BUILD_ID is set and the composable-agents version cannot "
                "be read from installed package metadata (source checkout or an image "
                "without distribution metadata). Set CA_WORKER_BUILD_ID to a stable, "
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
    module_name, sep, attr_path = spec.partition(":")
    if not sep or not module_name or not attr_path:
        raise ValueError(f"context factory spec must be 'module:attr', got {spec!r}")
    try:
        target: Any = import_module(module_name)
    except ImportError as exc:
        raise ValueError(f"cannot import context factory module {module_name!r}: {exc}") from exc
    for part in attr_path.split("."):
        try:
            target = getattr(target, part)
        except AttributeError as exc:
            raise ValueError(
                f"context factory {spec!r}: module {module_name!r} has no attribute {attr_path!r}"
            ) from exc
    if not callable(target):
        raise ValueError(f"context factory {spec!r} is not callable")
    return target  # type: ignore[no-any-return]


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
        raise ComposableAgentsError(
            f"context factory {spec!r} must return a WorkerContext, "
            f"got {type(context).__name__}"
        )
    return context


async def serve(
    settings: WorkerServeSettings,
    *,
    shutdown_event: Optional[asyncio.Event] = None,
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
        raise ComposableAgentsError(
            "serve() requires temporalio; install 'composable-agents[temporal]'"
        ) from exc
    from .worker import build_worker

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
        context = await _resolve_context(settings.context_factory)

        connect_kwargs: dict[str, Any] = {
            "namespace": settings.namespace,
            # Always pass tls explicitly: the SDK auto-enables TLS whenever
            # api_key is set and tls is left unset, which would silently
            # override an explicit TEMPORAL_TLS=false.
            "tls": settings.tls,
        }
        if settings.api_key is not None:
            connect_kwargs["api_key"] = settings.api_key
        client = await Client.connect(settings.address, **connect_kwargs)

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


__all__ = [
    "DEFAULT_TASK_QUEUE",
    "HealthServer",
    "WorkerServeSettings",
    "load_context_factory",
    "serve",
]
