"""Full-stack live harness for the episode-summarizer example."""

from __future__ import annotations

import asyncio
import base64
import importlib
import io
import json
import logging
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, redirect_stderr, redirect_stdout, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

import httpx
import uvicorn
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from julep.app_deploy import publish_application
from julep.artifact_store import LocalDirArtifactStore
from julep.execution.effects import WorkerContext, configure
from julep.execution.projection_store import (
    PostgresExecutionStore,
    set_projection_store,
)
from julep.execution.serve import WorkerServeSettings, serve
from julep.mcp_auth import McpAuthConfig, http_mcp_caller

from . import tools_server

LIVE_ONE_LINER_MODEL = "anthropic:claude-haiku-4-5-20251001"
DEFAULT_SUMMARIZER_MODEL = "anthropic:claude-sonnet-5"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PAYLOAD_KEY_ID = "payload-k1"
_MCP_KEY_ID = "episodes-k1"
_MCP_ISSUER = "episode-summarizer-harness"


class HarnessUnavailable(RuntimeError):
    """A required external service or credential is unavailable."""


@dataclass(frozen=True)
class LiveE2EResult:
    run_id: str
    sse_event_count: int
    terminal_seen: bool
    result_value: Any
    summaries: dict[str, str]
    one_liners: dict[str, str]
    wall_seconds: float
    model_ids: dict[str, str]
    trace_output: str = ""


@dataclass
class _ManagedProcess:
    process: subprocess.Popen[str]
    log: TextIO
    log_path: Path


def free_port() -> int:
    """Reserve an ephemeral port long enough to discover its number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def docker_usable() -> bool:
    """Return whether the Docker daemon responds within a short deadline."""
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _wait_for_postgres(dsn: str, *, timeout_s: float) -> None:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise HarnessUnavailable("psycopg is required for the live harness") from exc

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(dsn, connect_timeout=2):
                return
        except psycopg.Error:
            time.sleep(0.25)
    raise HarnessUnavailable("ephemeral Postgres did not become ready")


def _remove_postgres_container(name: str) -> None:
    with suppress(OSError, subprocess.TimeoutExpired):
        subprocess.run(
            ["docker", "rm", "-f", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )


@contextmanager
def ephemeral_postgres() -> Iterator[str]:
    """Yield a configured DSN, or manage a disposable Postgres 16 container."""
    configured = os.environ.get("EPISODE_E2E_PG_DSN")
    if configured:
        yield configured
        return

    if not docker_usable():
        raise HarnessUnavailable("no postgres: set EPISODE_E2E_PG_DSN or start docker")

    name = f"julep-episode-summarizer-e2e-{uuid.uuid4().hex[:8]}"
    port = free_port()
    command = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        name,
        "-e",
        "POSTGRES_PASSWORD=julep",
        "-e",
        "POSTGRES_DB=julep",
        "-p",
        f"127.0.0.1:{port}:5432",
        "postgres:16",
    ]
    try:
        started = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _remove_postgres_container(name)
        raise HarnessUnavailable("docker could not start postgres:16") from exc
    if started.returncode != 0:
        _remove_postgres_container(name)
        raise HarnessUnavailable("docker could not start postgres:16")

    dsn = f"postgresql://postgres:julep@127.0.0.1:{port}/julep"
    try:
        _wait_for_postgres(dsn, timeout_s=40)
        yield dsn
    finally:
        _remove_postgres_container(name)


@contextmanager
def _temporary_environ(updates: Mapping[str, str]) -> Iterator[None]:
    previous = {name: os.environ.get(name) for name in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@contextmanager
def _quiet_transport_logs() -> Iterator[None]:
    loggers = [logging.getLogger("httpx"), logging.getLogger("mcp")]
    previous = [logger.level for logger in loggers]
    for logger in loggers:
        logger.setLevel(logging.WARNING)
    try:
        yield
    finally:
        for logger, level in zip(loggers, previous, strict=True):
            logger.setLevel(level)


def _public_key_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _spawn_process(
    command: Sequence[str],
    *,
    env: Mapping[str, str],
    log_path: Path,
) -> _ManagedProcess:
    log = log_path.open("w+", encoding="utf-8")
    try:
        process = subprocess.Popen(
            list(command),
            cwd=_REPO_ROOT,
            env=dict(env),
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    except Exception:
        log.close()
        raise
    return _ManagedProcess(process=process, log=log, log_path=log_path)


def _redact(text: str, secret_values: Sequence[str]) -> str:
    for value in secret_values:
        if value:
            text = text.replace(value, "<redacted>")
    return text


def _process_log_tail(
    managed: _ManagedProcess,
    *,
    secret_values: Sequence[str],
) -> str:
    with suppress(OSError):
        managed.log.flush()
    try:
        text = managed.log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return _redact(text[-8_000:], secret_values)


async def _terminate_process(managed: _ManagedProcess | None) -> None:
    if managed is None:
        return
    process = managed.process
    try:
        if process.poll() is None:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
            try:
                await asyncio.to_thread(process.wait, 10)
            except subprocess.TimeoutExpired:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                await asyncio.to_thread(process.wait, 10)
    finally:
        managed.log.close()


def _child_env(*, keep_payload_keys: bool = False) -> dict[str, str]:
    env = dict(os.environ)
    for name in (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "JULEP_API_KEY",
        "JULEP_API_KEYS",
        "JULEP_BUNDLE_SIGNING_KEY",
        "JULEP_BUNDLES",
        "JULEP_EXECUTION_STORE_DSN",
        "EPISODE_E2E_PG_DSN",
        "JULEP_MCP_SIGNING_KEY",
        "EPISODE_SUMMARIZER_MODEL",
        "EPISODE_TOOLS_URL",
        "EPISODE_ONE_LINER_MODEL",
        "JULEP_ARTIFACT_STORE_URL",
    ):
        env.pop(name, None)
    if not keep_payload_keys:
        env.pop("TEMPORAL_PAYLOAD_KEYS", None)
        env.pop("TEMPORAL_PAYLOAD_KEY_ID", None)
    return env


async def _wait_for_temporal(
    temporal_bin: str,
    address: str,
    managed: _ManagedProcess,
    *,
    secret_values: Sequence[str],
    timeout_s: float = 40,
) -> None:
    deadline = time.monotonic() + timeout_s
    command = [
        temporal_bin,
        "operator",
        "namespace",
        "describe",
        "--address",
        address,
        "--context-timeout",
        "2",
        "default",
    ]
    while time.monotonic() < deadline:
        if managed.process.poll() is not None:
            tail = _process_log_tail(managed, secret_values=secret_values)
            raise RuntimeError(f"Temporal exited during startup\n{tail}")
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=4,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result is not None and result.returncode == 0:
            return
        await asyncio.sleep(0.25)
    tail = _process_log_tail(managed, secret_values=secret_values)
    raise HarnessUnavailable(f"Temporal development server did not become ready\n{tail}")


class _ToolsServer:
    def __init__(self, host: str, port: int) -> None:
        config = uvicorn.Config(
            tools_server.build_app(),
            host=host,
            port=port,
            log_level="error",
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(
            target=self.server.run,
            name="episode-summarizer-tools-server",
            daemon=True,
        )

    async def start(self, *, timeout_s: float = 15) -> None:
        self.thread.start()
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.server.started:
                return
            if not self.thread.is_alive():
                raise RuntimeError("memory-tools server exited during startup")
            await asyncio.sleep(0.05)
        raise RuntimeError("memory-tools server did not become ready")

    async def stop(self) -> None:
        self.server.should_exit = True
        await asyncio.to_thread(self.thread.join, 10)
        if self.thread.is_alive():
            self.server.force_exit = True
            await asyncio.to_thread(self.thread.join, 5)
        if self.thread.is_alive():
            raise RuntimeError("memory-tools server did not stop")


async def _verify_tools_auth(url: str) -> None:
    async with httpx.AsyncClient(timeout=5) as client:
        unauthenticated = await client.post(
            url,
            headers={"Idempotency-Key": "unauthenticated-probe"},
            content=b"{}",
        )
    if unauthenticated.status_code != 401:
        raise RuntimeError(
            f"memory-tools accepted an unauthenticated request: HTTP {unauthenticated.status_code}"
        )

    caller = http_mcp_caller(
        {tools_server.MCP_SERVER: url},
        auth=McpAuthConfig.from_env(),
    )
    episode_id = tools_server.EPISODE_IDS[0]
    result = await caller(
        tools_server.MCP_SERVER,
        "read-episode",
        {"episode_id": episode_id},
        "authenticated-probe",
        {"tenant": "demo", "sub": "episode-summarizer-harness"},
    )
    if not isinstance(result, dict) or result.get("episodeId") != episode_id:
        raise RuntimeError("authenticated memory-tools probe returned an invalid result")


async def _wait_for_api(
    base_url: str,
    client_token: str,
    managed: _ManagedProcess,
    *,
    secret_values: Sequence[str],
    timeout_s: float = 40,
) -> None:
    deadline = time.monotonic() + timeout_s
    headers = {"Authorization": f"Bearer {client_token}"}
    async with httpx.AsyncClient(timeout=2) as client:
        while time.monotonic() < deadline:
            if managed.process.poll() is not None:
                tail = _process_log_tail(managed, secret_values=secret_values)
                raise RuntimeError(f"Julep API exited during startup\n{tail}")
            try:
                health = await client.get(f"{base_url}/v1/health")
                ready = await client.get(f"{base_url}/v1/ready", headers=headers)
            except httpx.HTTPError:
                await asyncio.sleep(0.25)
                continue
            if health.status_code == 200 and ready.status_code == 200:
                return
            await asyncio.sleep(0.25)
    tail = _process_log_tail(managed, secret_values=secret_values)
    raise RuntimeError(f"Julep API did not become ready\n{tail}")


def _require_status(
    response: httpx.Response,
    expected: Sequence[int],
    label: str,
    *,
    secret_values: Sequence[str],
) -> None:
    if response.status_code in expected:
        return
    body = _redact(response.text[:4_000], secret_values)
    raise RuntimeError(f"{label} failed: HTTP {response.status_code}: {body}")


async def _start_worker(
    settings: WorkerServeSettings,
) -> tuple[asyncio.Event, asyncio.Task[None]]:
    stop = asyncio.Event()
    ready = asyncio.Event()
    task = asyncio.create_task(
        serve(
            settings,
            shutdown_event=stop,
            ready_event=ready,
            verify_connection=True,
        ),
        name="episode-summarizer-worker",
    )
    ready_wait = asyncio.create_task(ready.wait())
    try:
        done, _pending = await asyncio.wait(
            {task, ready_wait},
            timeout=30,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if task in done:
            await task
        if not ready.is_set():
            raise RuntimeError("Julep worker did not become ready")
    except BaseException:
        stop.set()
        if not task.done():
            try:
                await asyncio.wait_for(task, timeout=10)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
        raise
    finally:
        ready_wait.cancel()
        with suppress(asyncio.CancelledError):
            await ready_wait
    return stop, task


async def _stop_worker(
    stop: asyncio.Event | None,
    task: asyncio.Task[None] | None,
) -> None:
    if stop is None or task is None:
        return
    stop.set()
    try:
        await asyncio.wait_for(task, timeout=40)
    except asyncio.TimeoutError:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


async def _consume_sse(
    client: httpx.AsyncClient,
    run_id: str,
    *,
    timeout_s: float,
) -> tuple[int, bool]:
    async def consume() -> tuple[int, bool]:
        event_count = 0
        current_event = ""
        async with client.stream(
            "GET",
            f"/v1/runs/{run_id}/events",
            headers={"Accept": "text/event-stream"},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    current_event = line.partition(":")[2].strip()
                    if current_event == "projection":
                        event_count += 1
                elif line.startswith("data:") and current_event == "projection":
                    payload = json.loads(line.partition(":")[2].strip())
                    attrs = payload.get("attrs")
                    if isinstance(attrs, dict) and attrs.get("terminal") is True:
                        return event_count, True
                elif line == "":
                    current_event = ""
        return event_count, False

    return await asyncio.wait_for(consume(), timeout=timeout_s)


async def _capture_remote_trace(
    run_id: str,
    *,
    base_url: str,
    client_token: str,
) -> str:
    def invoke() -> tuple[int, str]:
        from julep.cli.main import main as cli_main

        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli_main(
                [
                    "trace",
                    run_id,
                    "--remote",
                    "--api-url",
                    base_url,
                    "--api-key",
                    client_token,
                ]
            )
        return code, stdout.getvalue() + stderr.getvalue()

    code, output = await asyncio.to_thread(invoke)
    if code != 0:
        raise RuntimeError(f"remote trace failed with exit code {code}")
    return output.strip()


def _bundle_entries(release: Any) -> str:
    entries: list[str] = []
    for pipeline in release.pipelines:
        for ref in pipeline.bundle_ref or ():
            entries.append(f"{ref['bundleHash']}:{ref['signatureDigest']}")
    return ",".join(entries)


def _result_surfaces() -> tuple[dict[str, str], dict[str, str]]:
    snapshot = tools_server.store_snapshot()
    summaries: dict[str, str] = {}
    one_liners: dict[str, str] = {}
    for episode_id in tools_server.EPISODE_IDS:
        row = snapshot[episode_id]
        summary = row.get("summary")
        one_liner = row.get("oneLiner")
        if isinstance(summary, str):
            summaries[episode_id] = summary
        if isinstance(one_liner, str):
            one_liners[episode_id] = one_liner
    return summaries, one_liners


def _assert_live_invariants(
    *,
    run_status: str,
    sse_event_count: int,
    terminal_seen: bool,
    result_value: Any,
    summaries: Mapping[str, str],
    one_liners: Mapping[str, str],
) -> None:
    if run_status != "completed":
        raise AssertionError(f"run finished with status {run_status!r}")
    if sse_event_count < 1 or not terminal_seen:
        raise AssertionError("SSE stream did not include a terminal projection event")
    expected = set(tools_server.EPISODE_IDS)
    if set(summaries) != expected or not all(summaries.values()):
        raise AssertionError("not every found episode received a non-empty summary")
    if set(one_liners) != expected or not all(one_liners.values()):
        raise AssertionError("not every found episode received a non-empty one-liner")
    if not isinstance(result_value, dict):
        raise AssertionError("batch result is not an object")
    results = result_value.get("results")
    if not isinstance(results, list):
        raise AssertionError("batch result has no results list")
    missing = next(
        (
            item
            for item in results
            if isinstance(item, dict) and item.get("episodeId") == tools_server.MISSING_EPISODE_ID
        ),
        None,
    )
    if not isinstance(missing, dict) or (
        missing.get("summaryStatus"),
        missing.get("oneLinerStatus"),
    ) != ("not_found", "not_found"):
        raise AssertionError("the deliberately absent episode did not take the not-found branch")


async def _cleanup_runtime(
    *,
    worker_stop: asyncio.Event | None,
    worker_task: asyncio.Task[None] | None,
    tools: _ToolsServer | None,
    api_process: _ManagedProcess | None,
    temporal_process: _ManagedProcess | None,
    projection_store: PostgresExecutionStore | None,
) -> BaseException | None:
    errors: list[BaseException] = []

    try:
        await _stop_worker(worker_stop, worker_task)
    except BaseException as exc:
        errors.append(exc)
    try:
        if tools is not None:
            await tools.stop()
    except BaseException as exc:
        errors.append(exc)
    try:
        await _terminate_process(api_process)
    except BaseException as exc:
        errors.append(exc)
    try:
        await _terminate_process(temporal_process)
    except BaseException as exc:
        errors.append(exc)
    try:
        if projection_store is not None:
            projection_store.close()
    except BaseException as exc:
        errors.append(exc)
    try:
        set_projection_store(None)
        configure(WorkerContext())
    except BaseException as exc:
        errors.append(exc)
    return errors[0] if errors else None


async def run_live_e2e(
    *,
    summarizer_model: str | None = None,
    one_liner_model: str = LIVE_ONE_LINER_MODEL,
    timeout_s: float = 180,
) -> LiveE2EResult:
    """Run the published application through Temporal and the HTTP control plane."""
    started_at = time.monotonic()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HarnessUnavailable("ANTHROPIC_API_KEY is required for the live harness")
    temporal_bin = shutil.which("temporal")
    if temporal_bin is None:
        raise HarnessUnavailable("the temporal CLI is required for the live harness")

    resolved_summarizer = (
        summarizer_model or os.environ.get("EPISODE_SUMMARIZER_MODEL") or DEFAULT_SUMMARIZER_MODEL
    )
    if not resolved_summarizer.startswith("anthropic:"):
        raise HarnessUnavailable("the live summarizer model must use Anthropic")
    if not one_liner_model.startswith("anthropic:"):
        raise HarnessUnavailable("the live one-liner model must use Anthropic")

    with _quiet_transport_logs(), ephemeral_postgres() as dsn:
        with tempfile.TemporaryDirectory(prefix="julep-episode-summarizer-e2e-") as temp_dir:
            temp_root = Path(temp_dir)
            artifact_dir = temp_root / "artifacts"
            artifact_dir.mkdir()
            store_url = artifact_dir.resolve().as_uri()

            mcp_seed = os.urandom(32).hex()
            mcp_private = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(mcp_seed))
            mcp_public = base64.b64encode(_public_key_bytes(mcp_private)).decode("ascii")
            bundle_seed = os.urandom(32).hex()
            bundle_private = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(bundle_seed))
            bundle_public = _public_key_bytes(bundle_private).hex()
            payload_key = os.urandom(32).hex()
            payload_keyring = f"{_PAYLOAD_KEY_ID}={payload_key}"
            admin_token = secrets.token_urlsafe(24)
            client_token = secrets.token_urlsafe(24)

            temporal_port = free_port()
            temporal_http_port = free_port()
            temporal_metrics_port = free_port()
            tools_port = free_port()
            api_port = free_port()
            temporal_address = f"127.0.0.1:{temporal_port}"
            tools_url = f"http://127.0.0.1:{tools_port}/mcp"
            api_url = f"http://127.0.0.1:{api_port}"

            environment = {
                "JULEP_MCP_SIGNING_KEY": mcp_seed,
                "JULEP_MCP_VERIFY_KEYS": f"{_MCP_KEY_ID}:{mcp_public}",
                "JULEP_MCP_ISSUER": _MCP_ISSUER,
                "JULEP_MCP_KID": _MCP_KEY_ID,
                "JULEP_MCP_TTL_S": "300",
                "JULEP_BUNDLE_ALLOWED_SIGNERS": bundle_public,
                "JULEP_BUNDLES": "",
                "JULEP_ARTIFACT_STORE_URL": store_url,
                "EPISODE_TOOLS_URL": tools_url,
                "EPISODE_SUMMARIZER_MODEL": resolved_summarizer,
                # The code default remains OpenAI; live runs override it because
                # this environment's OpenAI credential is intentionally invalid.
                "EPISODE_ONE_LINER_MODEL": one_liner_model,
                "JULEP_EXECUTION_STORE_DSN": dsn,
                "TEMPORAL_PAYLOAD_KEYS": payload_keyring,
                "TEMPORAL_PAYLOAD_KEY_ID": _PAYLOAD_KEY_ID,
            }
            secret_values = [
                os.environ.get("ANTHROPIC_API_KEY", ""),
                os.environ.get("OPENAI_API_KEY", ""),
                mcp_seed,
                bundle_seed,
                payload_key,
                admin_token,
                client_token,
                dsn,
            ]

            temporal_process: _ManagedProcess | None = None
            api_process: _ManagedProcess | None = None
            tools: _ToolsServer | None = None
            worker_stop: asyncio.Event | None = None
            worker_task: asyncio.Task[None] | None = None
            projection_store: PostgresExecutionStore | None = None

            with _temporary_environ(environment):
                try:
                    temporal_process = _spawn_process(
                        [
                            temporal_bin,
                            "server",
                            "start-dev",
                            "--headless",
                            "--ip",
                            "127.0.0.1",
                            "--port",
                            str(temporal_port),
                            "--http-port",
                            str(temporal_http_port),
                            "--metrics-port",
                            str(temporal_metrics_port),
                            "--log-level",
                            "error",
                            "--namespace",
                            "default",
                        ],
                        env=_child_env(),
                        log_path=temp_root / "temporal.log",
                    )
                    await _wait_for_temporal(
                        temporal_bin,
                        temporal_address,
                        temporal_process,
                        secret_values=secret_values,
                    )

                    tools_server.reset()
                    tools = _ToolsServer("127.0.0.1", tools_port)
                    await tools.start()
                    await _verify_tools_auth(tools_url)

                    flow_module = importlib.import_module("examples.episode_summarizer.flow")
                    if flow_module.SUMMARIZER_R.model != resolved_summarizer or (
                        flow_module.ONE_LINER_R.model != one_liner_model
                    ):
                        raise RuntimeError(
                            "examples.episode_summarizer.flow was imported before live model overrides"
                        )
                    compiled = flow_module.build_application().compile()
                    release = publish_application(
                        compiled,
                        LocalDirArtifactStore(artifact_dir),
                        worker_image="local/episode-summarizer@sha256:" + "0" * 64,
                        deployment_config={"queues": {flow_module.LANE: flow_module.LANE}},
                        signing_key=bundle_seed,
                    )
                    task_queue = release.pipelines[0].task_queue
                    if task_queue is None:
                        raise RuntimeError("published release has no pinned task queue")
                    os.environ["JULEP_BUNDLES"] = _bundle_entries(release)

                    server_env = _child_env(keep_payload_keys=True)
                    server_env.update(
                        {
                            "JULEP_API_KEYS": (f"admin:{admin_token}:admin,client:{client_token}"),
                            "JULEP_EXECUTION_STORE_DSN": dsn,
                            "JULEP_ARTIFACT_STORE_URL": store_url,
                            "TEMPORAL_ADDRESS": temporal_address,
                            "TEMPORAL_NAMESPACE": "default",
                            "TEMPORAL_TLS": "false",
                            "JULEP_SERVER_HOST": "127.0.0.1",
                            "JULEP_SERVER_PORT": str(api_port),
                            "TEMPORAL_PAYLOAD_KEYS": payload_keyring,
                            "TEMPORAL_PAYLOAD_KEY_ID": _PAYLOAD_KEY_ID,
                            "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "true",
                        }
                    )
                    api_process = _spawn_process(
                        [
                            sys.executable,
                            "-m",
                            "julep.cli.main",
                            "serve",
                            "api",
                            "--migrate",
                        ],
                        env=server_env,
                        log_path=temp_root / "api.log",
                    )
                    await _wait_for_api(
                        api_url,
                        client_token,
                        api_process,
                        secret_values=secret_values,
                    )

                    admin_headers = {"Authorization": f"Bearer {admin_token}"}
                    async with httpx.AsyncClient(base_url=api_url, timeout=30) as admin:
                        published = await admin.post(
                            "/v1/releases",
                            content=release.manifest_bytes,
                            headers={
                                **admin_headers,
                                "Content-Type": "application/octet-stream",
                            },
                        )
                        _require_status(
                            published,
                            (200, 201),
                            "release publication",
                            secret_values=secret_values,
                        )
                        activated = await admin.post(
                            "/v1/deployments",
                            json={"lane": flow_module.LANE, "release": release.release_hash},
                            headers=admin_headers,
                        )
                        _require_status(
                            activated,
                            (200, 201),
                            "deployment activation",
                            secret_values=secret_values,
                        )

                    projection_store = PostgresExecutionStore(dsn)
                    set_projection_store(projection_store)
                    worker_settings = WorkerServeSettings(
                        context_factory=("examples.episode_summarizer.worker_context:make_context"),
                        address=temporal_address,
                        namespace="default",
                        task_queue=task_queue,
                        payload_keys=payload_keyring,
                        payload_key_id=_PAYLOAD_KEY_ID,
                        payload_encryption_required=True,
                        graceful_shutdown_s=20,
                    )
                    worker_stop, worker_task = await _start_worker(worker_settings)

                    client_headers = {"Authorization": f"Bearer {client_token}"}
                    async with httpx.AsyncClient(
                        base_url=api_url,
                        headers=client_headers,
                        timeout=httpx.Timeout(timeout_s + 30, connect=10),
                    ) as client:
                        started = await client.post(
                            "/v1/runs",
                            json={
                                "pipeline": flow_module.PIPELINE_NAME,
                                "input": [
                                    *tools_server.EPISODE_IDS,
                                    tools_server.MISSING_EPISODE_ID,
                                ],
                                "principal": {
                                    "tenant": "demo",
                                    "sub": "episode-summarizer-harness",
                                },
                            },
                            headers={"Idempotency-Key": uuid.uuid4().hex},
                        )
                        _require_status(
                            started,
                            (200, 201),
                            "run start",
                            secret_values=secret_values,
                        )
                        run_id = str(started.json()["run_id"])
                        sse_event_count, terminal_seen = await _consume_sse(
                            client,
                            run_id,
                            timeout_s=timeout_s,
                        )
                        result_response = await client.get(
                            f"/v1/runs/{run_id}/result",
                            params={"wait_s": 30},
                        )
                        _require_status(
                            result_response,
                            (200,),
                            "run result",
                            secret_values=secret_values,
                        )
                        result_payload = result_response.json()

                    trace_output = await _capture_remote_trace(
                        run_id,
                        base_url=api_url,
                        client_token=client_token,
                    )
                    run_status = str(result_payload["run"]["status"])
                    result_value = result_payload.get("result")
                    summaries, one_liners = _result_surfaces()
                    _assert_live_invariants(
                        run_status=run_status,
                        sse_event_count=sse_event_count,
                        terminal_seen=terminal_seen,
                        result_value=result_value,
                        summaries=summaries,
                        one_liners=one_liners,
                    )
                    return LiveE2EResult(
                        run_id=run_id,
                        sse_event_count=sse_event_count,
                        terminal_seen=terminal_seen,
                        result_value=result_value,
                        summaries=summaries,
                        one_liners=one_liners,
                        wall_seconds=time.monotonic() - started_at,
                        model_ids={
                            "summarizer": resolved_summarizer,
                            "one_liner": one_liner_model,
                        },
                        trace_output=trace_output,
                    )
                finally:
                    active_exception = sys.exc_info()[1]
                    cleanup_error = await _cleanup_runtime(
                        worker_stop=worker_stop,
                        worker_task=worker_task,
                        tools=tools,
                        api_process=api_process,
                        temporal_process=temporal_process,
                        projection_store=projection_store,
                    )
                    if cleanup_error is not None and active_exception is None:
                        raise RuntimeError("episode-summarizer harness cleanup failed") from cleanup_error


__all__ = [
    "DEFAULT_SUMMARIZER_MODEL",
    "HarnessUnavailable",
    "LIVE_ONE_LINER_MODEL",
    "LiveE2EResult",
    "docker_usable",
    "ephemeral_postgres",
    "free_port",
    "run_live_e2e",
]
