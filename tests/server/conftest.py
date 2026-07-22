from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from julep.app_deploy import ApplicationRelease, PipelineRelease
from julep.artifact_store import LocalDirArtifactStore
from julep.execution.projection_store import InMemoryExecutionStore
from julep.server.app import create_app
from julep.server.auth import ApiKey
from julep.server.settings import ServerSettings
from julep.server.temporal import TemporalStartAmbiguous


class FakeTemporalGateway:
    def __init__(self) -> None:
        self.starts: list[dict[str, Any]] = []
        self.canceled: list[str] = []
        self.terminated: list[str] = []
        self.signals: list[tuple[str, str, Any]] = []
        self.queries: list[tuple[str, str]] = []
        self.descriptions: dict[str, str | Exception] = {}
        self.query_result: Any = []
        self.fail_start = False
        self.ambiguous_start = False
        self.is_ready = True

    async def start_flow(
        self,
        pipeline: PipelineRelease,
        *,
        workflow_id: str,
        run_id: str,
        input: Any,
        principal: dict[str, Any],
        queue_lanes: dict[str, str] | None,
        secrets: dict[str, str] | None,
    ) -> str:
        if self.ambiguous_start:
            raise TemporalStartAmbiguous("unconfirmed")
        if self.fail_start:
            raise RuntimeError("simulated Temporal start failure")
        self.starts.append(
            {
                "pipeline": pipeline,
                "workflow_id": workflow_id,
                "run_id": run_id,
                "input": input,
                "principal": principal,
                "secrets": secrets,
                "queue_lanes": queue_lanes,
            }
        )
        return f"temporal-{run_id}"

    async def cancel(self, workflow_id: str) -> None:
        self.canceled.append(workflow_id)

    async def terminate(self, workflow_id: str) -> None:
        self.terminated.append(workflow_id)

    async def describe(self, workflow_id: str) -> str:
        result = self.descriptions.get(workflow_id, "running")
        if isinstance(result, Exception):
            raise result
        return result

    async def signal(self, workflow_id: str, name: str, arg: Any) -> None:
        self.signals.append((workflow_id, name, arg))

    async def query(self, workflow_id: str, name: str) -> Any:
        self.queries.append((workflow_id, name))
        return self.query_result

    async def ready(self) -> bool:
        return self.is_ready


@dataclass
class ServerHarness:
    app: Any
    store: InMemoryExecutionStore
    gateway: FakeTemporalGateway
    artifacts: LocalDirArtifactStore
    settings: ServerSettings


@pytest.fixture
def server_factory(tmp_path: Path):
    counter = 0

    def build(
        *,
        store: InMemoryExecutionStore | None = None,
        gateway: FakeTemporalGateway | None = None,
        artifacts: LocalDirArtifactStore | None = None,
        reconciler: Any = None,
        queue_by_lane: dict[str, str] | None = None,
        enable_reconciler: bool = False,
        payload_encryption_required: bool = True,
    ) -> ServerHarness:
        nonlocal counter
        counter += 1
        resolved_store = store or InMemoryExecutionStore()
        resolved_gateway = gateway or FakeTemporalGateway()
        resolved_artifact_store = artifacts or LocalDirArtifactStore(tmp_path / f"artifacts-{counter}")
        settings = ServerSettings(
            api_keys=(
                ApiKey("alice", "alice-token"),
                ApiKey("bob", "bob-token"),
                ApiKey("admin", "admin-token", admin=True),
                ApiKey("worker", "worker-token", role="worker"),
            ),
            vault_keys="vault=" + "11" * 32,
            vault_key_id="vault",
            worker_secret_allowlist=frozenset({"tracker-token", "other-token"}),
            queue_by_lane=queue_by_lane or {},
            payload_encryption_required=payload_encryption_required,
            config_root=tmp_path,
        )
        app = create_app(
            settings=settings,
            store=resolved_store,
            gateway=resolved_gateway,
            artifacts=resolved_artifact_store,
            reconciler=reconciler,
            enable_reconciler=enable_reconciler,
            reconcile_interval_s=0.01,
            sse_heartbeat_seconds=1,
            sse_poll_seconds=0.001,
        )
        return ServerHarness(app, resolved_store, resolved_gateway, resolved_artifact_store, settings)

    return build


def make_release(
    *,
    marker: str = "a",
    bundle_ref: list[dict[str, str]] | None = None,
    runtime_declarations_ref: dict[str, Any] | None = None,
    mcp_preflight_policy: str | None = "pin",
) -> ApplicationRelease:
    return ApplicationRelease(
        application="memory",
        application_artifact_hash="sha256:" + marker * 64,
        worker_image="registry.example/memory@sha256:" + marker * 64,
        pipelines=(
            PipelineRelease(
                name="summary",
                lane="summary",
                artifact_hash="sha256:" + marker * 64,
                flow_json={"id": "root", "op": "IDENT"},
                manifest_json={},
                pinned_pures={},
                bundle_ref=bundle_ref,
                eval_packages=(),
                runtime_declarations_ref=runtime_declarations_ref,
                max_call_limits={},
                mcp_preflight_policy=mcp_preflight_policy,
            ),
        ),
    )


ALICE_HEADERS = {"Authorization": "Bearer alice-token"}
BOB_HEADERS = {"Authorization": "Bearer bob-token"}
ADMIN_HEADERS = {"Authorization": "Bearer admin-token"}
WORKER_HEADERS = {"Authorization": "Bearer worker-token"}
