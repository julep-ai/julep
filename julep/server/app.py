"""FastAPI application factory for the Julep execution control plane."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any, Optional

from fastapi import FastAPI

from ..app_deploy import LaneReconciler
from ..artifact_store import ArtifactStore
from ..execution.projection_store import ExecutionStore, SecretCipher
from .auth import KeyRing
from .routes.artifacts import router as artifacts_router
from .routes.deployments import router as deployments_router
from .routes.health import router as health_router
from .routes.releases import router as releases_router
from .routes.runs import reconcile_runs_once, router as runs_router
from .routes.secrets import router as secrets_router
from .settings import ServerSettings
from .sse import DEFAULT_HEARTBEAT_SECONDS, DEFAULT_POLL_SECONDS
from .temporal import TemporalGateway

logger = logging.getLogger("julep.server")


async def _reconcile_loop(
    store: ExecutionStore,
    app: FastAPI,
    interval_s: float,
) -> None:
    while True:
        gateway = app.state.gateway
        if gateway is not None:
            try:
                await reconcile_runs_once(store, gateway)
            except Exception as exc:
                # Credentials and request data are intentionally absent from
                # this process-level diagnostic.
                logger.warning("run reconciliation failed: %s", type(exc).__name__)
        await asyncio.sleep(interval_s)


async def _close_optional(target: object) -> None:
    close = getattr(target, "close", None)
    if not callable(close):
        return
    result = close()
    if inspect.isawaitable(result):
        await result


def create_app(
    *,
    settings: Optional[ServerSettings] = None,
    store: Optional[ExecutionStore] = None,
    gateway: Optional[TemporalGateway] = None,
    artifacts: Optional[ArtifactStore] = None,
    reconciler: Optional[LaneReconciler] = None,
    keyring: Optional[KeyRing] = None,
    vault_cipher: Optional[SecretCipher] = None,
    enable_reconciler: bool = True,
    reconcile_interval_s: Optional[float] = None,
    sse_heartbeat_seconds: int = DEFAULT_HEARTBEAT_SECONDS,
    sse_poll_seconds: float = DEFAULT_POLL_SECONDS,
) -> FastAPI:
    """Build an application; every external dependency is injectable for tests."""

    resolved_settings = settings or ServerSettings.from_env()
    resolved_store = store or resolved_settings.build_store()
    resolved_artifact_store = artifacts or resolved_settings.build_artifact_store()
    resolved_reconciler = (
        reconciler if reconciler is not None else resolved_settings.build_reconciler()
    )
    interval_s = (
        resolved_settings.reconcile_interval_s
        if reconcile_interval_s is None
        else reconcile_interval_s
    )
    if interval_s < 0:
        raise ValueError("reconcile_interval_s must be non-negative")
    if sse_heartbeat_seconds <= 0:
        raise ValueError("sse_heartbeat_seconds must be positive")
    if sse_poll_seconds <= 0:
        raise ValueError("sse_poll_seconds must be positive")

    resolved_keyring = keyring or KeyRing.from_settings(resolved_settings)
    resolved_vault_cipher = (
        vault_cipher if vault_cipher is not None else resolved_settings.build_vault_cipher()
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.gateway_error = None
        if app.state.gateway is None:
            try:
                app.state.gateway = await resolved_settings.build_gateway()
            except Exception as exc:
                app.state.gateway_error = f"{type(exc).__name__}: {exc}"
                logger.warning("Temporal connection failed: %s", type(exc).__name__)

        current_gateway = app.state.gateway
        start = getattr(current_gateway, "start", None)
        if callable(start):
            result = start()
            if inspect.isawaitable(result):
                await result

        installed_sighup = resolved_keyring.install_sighup_handler()
        task: Optional[asyncio.Task[None]] = None
        if enable_reconciler and interval_s > 0:
            task = asyncio.create_task(
                _reconcile_loop(resolved_store, app, interval_s),
                name="julep-run-reconciler",
            )
        app.state.reconcile_task = task
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            if installed_sighup:
                resolved_keyring.restore_sighup_handler()
            closing_gateway: Any = app.state.gateway
            if closing_gateway is not None:
                await _close_optional(closing_gateway)
            resolved_store.close()

    app = FastAPI(title="Julep Control Plane", version="1", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.store = resolved_store
    app.state.gateway = gateway
    app.state.gateway_error = None
    app.state.artifacts = resolved_artifact_store
    app.state.keyring = resolved_keyring
    app.state.vault_cipher = resolved_vault_cipher
    app.state.reconciler = resolved_reconciler
    app.state.deployment_reconcile_status = {}
    app.state.sse_heartbeat_seconds = sse_heartbeat_seconds
    app.state.sse_poll_seconds = sse_poll_seconds
    app.state.reconcile_task = None

    app.include_router(health_router, prefix="/v1")
    app.include_router(artifacts_router, prefix="/v1")
    app.include_router(releases_router, prefix="/v1")
    app.include_router(deployments_router, prefix="/v1")
    app.include_router(runs_router, prefix="/v1")
    app.include_router(secrets_router, prefix="/v1")
    return app


__all__ = ["create_app"]
