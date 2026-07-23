from __future__ import annotations

import asyncio
from typing import Any

import pytest

from julep.app_deploy import ApplicationRelease, PipelineRelease
from julep.execution.policy import ExecutionPolicy
from julep.server.settings import ServerSettings
from julep.server.temporal import TemporalClientGateway, create_temporal_gateway


def _pipeline() -> PipelineRelease:
    release = ApplicationRelease(
        application="memory",
        application_artifact_hash="sha256:" + "b" * 64,
        worker_image="registry.example/memory@sha256:" + "c" * 64,
        pipelines=(
            PipelineRelease(
                name="summary",
                lane="summary",
                artifact_hash="sha256:" + "d" * 64,
                flow_json={"id": "root", "op": "IDENT"},
                manifest_json={},
                pinned_pures={"pure": "sha256:" + "e" * 64},
                bundle_ref=None,
                eval_packages=(),
                max_call_limits={"tool": 2},
            ),
        ),
    )
    return release.pipelines[0]


def test_gateway_starts_harness_with_projection_and_reject_duplicate(
    monkeypatch,
) -> None:
    pytest.importorskip("temporalio")
    captured: dict[str, Any] = {}

    class Handle:
        run_id = "temporal-run"

    async def fake_start_flow(client: object, flow_json: object, manifest: object, **kwargs: Any):
        captured.update(
            client=client,
            flow_json=flow_json,
            manifest=manifest,
            kwargs=kwargs,
        )
        return Handle()

    monkeypatch.setattr("julep.execution.harness.start_flow", fake_start_flow)
    client = object()
    settings = ServerSettings(
        projection_batch_size=7,
        projection_batch_interval_s=0.5,
        payload_encryption_required=False,
    )
    gateway = TemporalClientGateway(client, settings)

    temporal_run_id = asyncio.run(
        gateway.start_flow(
            _pipeline(),
            workflow_id="run-api-id",
            run_id="api-id",
            input={"question": "hello"},
            principal={"key": "alice"},
            queue_lanes={"summary": "queue"},
            secrets={"tracker-token": "run-secret"},
        )
    )

    assert temporal_run_id == "temporal-run"
    kwargs = captured["kwargs"]
    assert kwargs["session_id"] == "run-api-id"
    assert kwargs["run_id"] == "api-id"
    assert kwargs["emit_projection"] is True
    assert kwargs["projection_batch_size"] == 7
    assert kwargs["projection_batch_interval_s"] == 0.5
    assert kwargs["principal"] == {"key": "alice"}
    assert kwargs["secrets"] == {"tracker-token": "run-secret"}
    assert kwargs["workflow_start_options"]["id_reuse_policy"].name == "REJECT_DUPLICATE"


def test_gateway_threads_release_execution_policy(monkeypatch) -> None:
    pytest.importorskip("temporalio")
    captured: dict[str, Any] = {}

    class Handle:
        run_id = "temporal-run"

    async def fake_start_flow(client: object, flow_json: object, manifest: object, **kwargs: Any):
        captured.update(kwargs=kwargs)
        return Handle()

    monkeypatch.setattr("julep.execution.harness.start_flow", fake_start_flow)
    policy = ExecutionPolicy(reasoner_max_attempts=1, reasoner_timeout_s=300)
    release = ApplicationRelease(
        application="memory",
        application_artifact_hash="sha256:" + "b" * 64,
        worker_image=None,
        pipelines=(
            PipelineRelease(
                name="summary",
                lane="summary",
                artifact_hash="sha256:" + "d" * 64,
                flow_json={"id": "root", "op": "IDENT"},
                manifest_json={},
                pinned_pures={},
                bundle_ref=None,
                eval_packages=(),
                max_call_limits={},
                execution_policy=policy,
            ),
        ),
        deployment_config={"queues": {"summary": "summary"}},
    )
    gateway = TemporalClientGateway(
        object(),
        ServerSettings(payload_encryption_required=False),
    )

    asyncio.run(
        gateway.start_flow(
            release.pipelines[0],
            workflow_id="run-id",
            run_id="id",
            input={},
            principal={"key": "alice"},
            queue_lanes={"summary": "queue"},
            secrets=None,
        )
    )

    assert captured["kwargs"]["policy"] == policy


def test_temporal_factory_passes_explicit_connection_settings(monkeypatch) -> None:
    pytest.importorskip("temporalio")
    from temporalio.client import Client

    captured: dict[str, Any] = {}
    client = object()

    async def connect(address: str, **kwargs: Any) -> object:
        captured["address"] = address
        captured["kwargs"] = kwargs
        return client

    monkeypatch.setattr(Client, "connect", staticmethod(connect))
    settings = ServerSettings(
        temporal_address="temporal.example:7233",
        temporal_namespace="production",
        temporal_api_key="secret",
        temporal_tls=False,
        payload_encryption_required=False,
    )

    gateway = asyncio.run(create_temporal_gateway(settings))

    assert gateway.client is client
    assert captured == {
        "address": "temporal.example:7233",
        "kwargs": {
            "namespace": "production",
            "tls": False,
            "api_key": "secret",
        },
    }
