"""One-command supervisor for Julep's durable local development stack."""

from __future__ import annotations

import os
import signal
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol
from urllib.parse import urlsplit

from julep.cli.config import EnvConfig, JulepConfig


class DevStackError(RuntimeError):
    """The durable local stack is misconfigured or a child process failed."""


@dataclass(frozen=True)
class DevCommand:
    name: str
    argv: tuple[str, ...]
    environment: Mapping[str, str] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DevStackPlan:
    root: Path
    env_name: str
    api_url: str
    api_key: str = field(repr=False)
    temporal_address: str
    temporal: Optional[DevCommand]
    api: DevCommand
    worker: DevCommand
    publication_environment: Mapping[str, str] = field(repr=False)
    publish_release: bool = True
    start_workers: bool = True
    startup_timeout_s: float = 30.0


class ChildProcess(Protocol):
    def poll(self) -> Optional[int]: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    def wait(self, timeout: Optional[float] = None) -> int: ...


PopenFactory = Callable[..., ChildProcess]
ReleasePublisher = Callable[[DevStackPlan], tuple[tuple[str, str], ...]]


_RUNTIME_ENV_NAMES = frozenset(
    {
        "CURL_CA_BUNDLE",
        "HOME",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "LANG",
        "LOGNAME",
        "NO_PROXY",
        "PATH",
        "PATHEXT",
        "PYTHONPATH",
        "PYTHONUTF8",
        "PYTHONIOENCODING",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "TZ",
        "USER",
        "VIRTUAL_ENV",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)
_API_ENV_NAMES = frozenset(
    {
        "JULEP_API_KEYS",
        "JULEP_ARTIFACT_STORE_URL",
        "JULEP_BUNDLE_ALLOWED_SIGNERS",
        "JULEP_EXECUTION_STORE_DSN",
        "JULEP_PROJECTION_BATCH_INTERVAL_S",
        "JULEP_PROJECTION_BATCH_SIZE",
        "JULEP_SERVER_HELM_CHART",
        "JULEP_SERVER_HOST",
        "JULEP_SERVER_KUBERNETES_NAMESPACE",
        "JULEP_SERVER_PORT",
        "JULEP_SERVER_RECONCILE_INTERVAL_S",
        "JULEP_VAULT_KEY_ID",
        "JULEP_VAULT_KEYS",
        "JULEP_WORKER_SECRET_ALLOWLIST",
        "TEMPORAL_ADDRESS",
        "TEMPORAL_API_KEY",
        "TEMPORAL_NAMESPACE",
        "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED",
        "TEMPORAL_PAYLOAD_KEY_ID",
        "TEMPORAL_PAYLOAD_KEYS",
        "TEMPORAL_TLS",
    }
)
_WORKER_ENV_NAMES = frozenset(
    {
        "JULEP_ARTIFACT_STORE_URL",
        "JULEP_BLOB_STORE_URL",
        "JULEP_BUNDLE_ALLOWED_SIGNERS",
        "JULEP_EXECUTION_STORE_DSN",
        "JULEP_REDACTION",
        "JULEP_WORKER_BUILD_ID",
        "JULEP_WORKER_VERSIONING",
        "TEMPORAL_ADDRESS",
        "TEMPORAL_API_KEY",
        "TEMPORAL_NAMESPACE",
        "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED",
        "TEMPORAL_PAYLOAD_KEY_ID",
        "TEMPORAL_PAYLOAD_KEYS",
        "TEMPORAL_TLS",
        "WORKER_APPLICATION",
        "WORKER_CONTEXT_FACTORY",
        "WORKER_GRACEFUL_SHUTDOWN_S",
        "WORKER_HEALTH_PORT",
        "WORKER_MAX_CONCURRENT_ACTIVITIES",
        "WORKER_MAX_CONCURRENT_WORKFLOW_TASKS",
        "WORKER_RUNTIME_DECLARATIONS_HASH",
    }
)
_PUBLICATION_ENV_NAMES = frozenset(
    {
        "JULEP_ARTIFACT_STORE_URL",
        "JULEP_BUNDLE_SIGNING_KEY",
    }
)


def _selected_environment(
    source: Mapping[str, str],
    names: frozenset[str] = frozenset(),
) -> dict[str, str]:
    """Copy only role-owned configuration plus non-secret process plumbing."""

    selected = {
        name: value
        for name, value in source.items()
        if name in _RUNTIME_ENV_NAMES or name.startswith("LC_") or name in names
    }
    return selected


class _TerminationRequested(BaseException):
    """Internal control flow used to clean up children on SIGTERM."""


@contextmanager
def _sigterm_as_exception() -> Iterator[None]:
    """Turn SIGTERM into normal supervisor unwinding on the main thread."""

    if threading.current_thread() is not threading.main_thread():
        yield
        return
    previous = signal.getsignal(signal.SIGTERM)

    def terminate(_signum: int, _frame: object) -> None:
        raise _TerminationRequested

    signal.signal(signal.SIGTERM, terminate)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def _server_endpoint(api_url: str) -> tuple[str, int]:
    parsed = urlsplit(api_url)
    if parsed.scheme != "http" or not parsed.hostname:
        raise DevStackError("julep dev up requires an http:// API URL with a host")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise DevStackError("julep dev up API URL must not contain a path, query, or fragment")
    return parsed.hostname, parsed.port or 80


def _temporal_endpoint(address: str) -> tuple[str, int]:
    raw = address.removeprefix("http://").removeprefix("https://")
    host, separator, port_text = raw.rpartition(":")
    if not separator or not host:
        raise DevStackError("TEMPORAL_ADDRESS must use host:port for julep dev up")
    try:
        port = int(port_text)
    except ValueError as exc:
        raise DevStackError("TEMPORAL_ADDRESS port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise DevStackError("TEMPORAL_ADDRESS port must be between 1 and 65535")
    return host, port


def build_dev_stack_plan(
    cfg: JulepConfig,
    env: EnvConfig,
    *,
    api_url: str,
    api_key: str,
    source_env: Mapping[str, str],
    start_temporal: bool = True,
    publish_release: bool = True,
    start_workers: bool = True,
    startup_timeout_s: float = 30.0,
    python: str = sys.executable,
) -> DevStackPlan:
    """Validate configuration and construct the exact supervised commands."""

    if startup_timeout_s <= 0:
        raise DevStackError("startup timeout must be positive")
    if start_workers and not publish_release:
        raise DevStackError("workers require release publication; also pass --no-worker")
    if not api_key.strip():
        raise DevStackError("--api-key or JULEP_API_KEY is required")
    if env.release_store is None:
        raise DevStackError(f"env {env.name!r} requires release_store")
    host, port = _server_endpoint(api_url)
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise DevStackError("julep dev up only supervises a loopback API")

    # The caller's ambient environment is used for validation, but is not
    # wholesale inherited by children. Provider credentials belong in the
    # selected environment's worker_environment table and are handed only to
    # workers below.
    effective = dict(source_env)
    # JULEP_API_KEY is a client credential, not server configuration. Keep it
    # out of child environments so worker secret resolution never receives an
    # admin token by accident. A separately generated worker-role token is
    # installed below only for the worker processes.
    worker_api_key = effective.pop("JULEP_WORKER_API_KEY", None)
    effective.pop("JULEP_API_KEY", None)
    effective.pop("JULEP_API_URL", None)
    effective["JULEP_ARTIFACT_STORE_URL"] = env.release_store
    effective["JULEP_SERVER_HOST"] = host
    effective["JULEP_SERVER_PORT"] = str(port)
    temporal_address = env.temporal_address or effective.get("TEMPORAL_ADDRESS") or "localhost:7233"
    effective["TEMPORAL_ADDRESS"] = temporal_address
    effective["TEMPORAL_NAMESPACE"] = env.temporal_namespace

    context_factory = env.worker_context_factory or effective.get("WORKER_CONTEXT_FACTORY")
    if not context_factory:
        raise DevStackError(
            "durable local workers require WORKER_CONTEXT_FACTORY or "
            f"env.{env.name}.worker_context_factory"
        )
    effective["WORKER_CONTEXT_FACTORY"] = context_factory

    try:
        from julep.server.auth import KeyRing
        from julep.server.settings import ServerSettings

        settings = ServerSettings.from_env(effective, root=cfg.root)
    except (ImportError, ValueError) as exc:
        raise DevStackError(str(exc)) from exc
    if settings.execution_store_dsn is None:
        raise DevStackError("JULEP_EXECUTION_STORE_DSN is required")
    keyring = KeyRing(settings.api_keys)
    authenticated = keyring.authenticate(api_key)
    if authenticated is None or authenticated.role != "admin":
        raise DevStackError("the dev API key must match an admin entry in JULEP_API_KEYS")
    if worker_api_key:
        worker_identity = keyring.authenticate(worker_api_key)
        if worker_identity is None or worker_identity.role != "worker":
            raise DevStackError("JULEP_WORKER_API_KEY must match a worker entry in JULEP_API_KEYS")
    if settings.payload_encryption_required and settings.payload_keys is None:
        raise DevStackError("durable dev requires Temporal payload encryption keys")

    temporal_host, temporal_port = _temporal_endpoint(temporal_address)
    # Split generated credentials by process. Workers need the shared payload
    # codec and a worker-role API token, but never the server's static keyring,
    # vault decryption key, or bundle-signing private key.
    publication_environment = _selected_environment(
        effective,
        _PUBLICATION_ENV_NAMES,
    )
    api_environment = _selected_environment(effective, _API_ENV_NAMES)
    worker_environment = _selected_environment(effective, _WORKER_ENV_NAMES)
    worker_environment.update(env.worker_environment)
    for server_only in (
        "JULEP_API_KEYS",
        "JULEP_VAULT_KEYS",
        "JULEP_VAULT_KEY_ID",
        "JULEP_BUNDLE_SIGNING_KEY",
        "JULEP_API_KEY",
        "JULEP_API_URL",
        "JULEP_WORKER_API_KEY",
    ):
        worker_environment.pop(server_only, None)
    if worker_api_key:
        worker_environment["JULEP_API_URL"] = api_url
        worker_environment["JULEP_API_KEY"] = worker_api_key

    temporal_environment = _selected_environment(effective)

    temporal: Optional[DevCommand] = None
    if start_temporal:
        if temporal_host not in {"127.0.0.1", "localhost", "::1"}:
            raise DevStackError("--start-temporal requires a loopback TEMPORAL_ADDRESS")
        temporal = DevCommand(
            "temporal",
            (
                "temporal",
                "server",
                "start-dev",
                "--headless",
                "--port",
                str(temporal_port),
            ),
            temporal_environment,
        )

    base = (python, "-m", "julep.cli.main")
    api = DevCommand(
        "api",
        (*base, "serve", "api", "--migrate", "--host", host, "--port", str(port)),
        api_environment,
    )
    worker = DevCommand("worker", (*base, "worker"), worker_environment)
    return DevStackPlan(
        root=cfg.root,
        env_name=env.name,
        api_url=api_url,
        api_key=api_key,
        temporal_address=temporal_address,
        temporal=temporal,
        api=api,
        worker=worker,
        publication_environment=publication_environment,
        publish_release=publish_release,
        start_workers=start_workers,
        startup_timeout_s=startup_timeout_s,
    )


def render_dev_stack_plan(plan: DevStackPlan) -> str:
    """Human-readable command plan with credentials redacted."""

    commands = [item for item in (plan.temporal, plan.api) if item is not None]
    lines = [f"{item.name:8} {' '.join(item.argv)}" for item in commands]
    if plan.publish_release:
        lines.append(f"publish  env={plan.env_name} publish-only register={plan.api_url}")
    if plan.start_workers:
        lines.append(f"worker   {' '.join(plan.worker.argv)}  # one per published queue")
    return "\n".join(lines) + "\n"


def _publish_and_register(plan: DevStackPlan) -> tuple[tuple[str, str], ...]:
    """Publish once through Python APIs, register, and return exact queue names."""

    from julep.cli.application import (
        apply_configured_application,
        release_queue_lines,
    )
    from julep.cli.config import load_config
    from julep.client import JulepClient

    with _temporary_environment(plan.publication_environment):
        cfg = load_config(plan.root)
        if plan.env_name not in cfg.envs:
            raise DevStackError(f"unknown env {plan.env_name!r}")
        release, _lanes = apply_configured_application(
            cfg,
            cfg.envs[plan.env_name],
            publish_only=True,
        )
        client = JulepClient(plan.api_url, plan.api_key)
        try:
            client.publish_release(release.manifest_bytes)
        finally:
            client.close()
    queues = tuple(release_queue_lines(release))
    if not queues:
        raise DevStackError("published release contains no lane queues")
    print(f"release   {release.release_hash}")
    print(f"artifact  {release.application_artifact_hash}")
    for lane, queue in queues:
        print(f"queue     {lane:24} {queue}")
    print(f"registered {release.release_hash}")
    print("traffic   unchanged")
    return queues


@contextmanager
def _temporary_environment(values: Mapping[str, str]) -> Iterator[None]:
    previous = dict(os.environ)
    os.environ.clear()
    os.environ.update(values)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous)


def _wait_for_tcp(
    address: str,
    *,
    timeout_s: float,
    child: Optional[ChildProcess],
) -> None:
    host, port = _temporal_endpoint(address)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if child is not None and child.poll() is not None:
            raise DevStackError("Temporal dev server exited before becoming ready")
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.1)
    raise DevStackError(f"Temporal did not become ready at {address} within {timeout_s:g}s")


def _wait_for_api(
    api_url: str,
    api_key: str,
    *,
    timeout_s: float,
    child: ChildProcess,
) -> None:
    deadline = time.monotonic() + timeout_s
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/v1/ready",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise DevStackError("Julep API exited before becoming ready")
        try:
            with urllib.request.urlopen(request, timeout=0.5) as response:  # noqa: S310
                if response.status == 200:
                    return
        except (OSError, urllib.error.HTTPError, urllib.error.URLError):
            time.sleep(0.1)
    raise DevStackError(f"Julep API did not become ready within {timeout_s:g}s")


def _stop_children(children: Sequence[tuple[str, ChildProcess]]) -> None:
    for _name, child in reversed(children):
        try:
            if child.poll() is None:
                child.terminate()
        except Exception:  # noqa: BLE001 - continue cleaning the remaining children.
            pass
    for _name, child in reversed(children):
        try:
            running = child.poll() is None
        except Exception:  # noqa: BLE001 - make a best-effort kill below.
            running = True
        if not running:
            continue
        try:
            child.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            try:
                child.kill()
                child.wait(timeout=5.0)
            except Exception:  # noqa: BLE001 - no remaining cleanup avenue.
                pass
        except Exception:  # noqa: BLE001 - continue cleaning the remaining children.
            try:
                child.kill()
            except Exception:  # noqa: BLE001 - no remaining cleanup avenue.
                pass


def run_dev_stack(
    plan: DevStackPlan,
    *,
    popen: PopenFactory = subprocess.Popen,
    publish: ReleasePublisher = _publish_and_register,
    wait_temporal: Callable[..., None] = _wait_for_tcp,
    wait_api: Callable[..., None] = _wait_for_api,
    poll_interval_s: float = 0.25,
) -> None:
    """Run the plan in the foreground and tear down every child on exit."""

    if plan.temporal is not None and shutil.which(plan.temporal.argv[0]) is None:
        raise DevStackError(
            "temporal CLI was not found on PATH; install it or pass --no-start-temporal"
        )
    children: list[tuple[str, ChildProcess]] = []

    def start(command: DevCommand, *, extra: Optional[Mapping[str, str]] = None) -> ChildProcess:
        environment = dict(command.environment)
        if extra:
            environment.update(extra)
        child = popen(command.argv, cwd=plan.root, env=environment)
        children.append((command.name, child))
        return child

    try:
        with _sigterm_as_exception():
            temporal_child: Optional[ChildProcess] = None
            if plan.temporal is not None:
                temporal_child = start(plan.temporal)
            wait_temporal(
                plan.temporal_address,
                timeout_s=plan.startup_timeout_s,
                child=temporal_child,
            )

            api_child = start(plan.api)
            wait_api(
                plan.api_url,
                plan.api_key,
                timeout_s=plan.startup_timeout_s,
                child=api_child,
            )
            queues = publish(plan) if plan.publish_release else ()
            worker_count = 0
            if plan.start_workers:
                for lane, queue in queues:
                    child = start(
                        DevCommand(
                            f"worker:{lane}",
                            plan.worker.argv,
                            plan.worker.environment,
                        ),
                        extra={"TEMPORAL_TASK_QUEUE": queue},
                    )
                    returncode = child.poll()
                    if returncode is not None:
                        raise DevStackError(
                            f"worker:{lane} exited with status {returncode} during startup"
                        )
                    worker_count += 1
            print(
                f"Julep durable dev stack ready: {plan.api_url} "
                f"({worker_count} worker{'s' if worker_count != 1 else ''})"
            )
            while True:
                for name, child in children:
                    returncode = child.poll()
                    if returncode is not None:
                        raise DevStackError(f"{name} exited with status {returncode}")
                time.sleep(poll_interval_s)
    except (KeyboardInterrupt, _TerminationRequested):
        return
    finally:
        _stop_children(children)


__all__ = [
    "DevCommand",
    "DevStackError",
    "DevStackPlan",
    "build_dev_stack_plan",
    "render_dev_stack_plan",
    "run_dev_stack",
]
