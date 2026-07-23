from __future__ import annotations

import asyncio
import time

import httpx
import pytest
from starlette.testclient import TestClient

import julep.server as server
from julep.client import (
    AsyncJulepClient,
    JulepClient,
    JulepClientError,
    JulepRunFailed,
    JulepRunTimeout,
)
from julep.projection import EventType, ProjectionEvent

pytest.importorskip("fastapi")


def _seed_run(store, run_id: str) -> None:
    assert store.create_run(
        run_id=run_id,
        idempotency_key=f"idem-{run_id}",
        workflow_id=f"run-{run_id}",
        session_id=f"run-{run_id}",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": "alice"},
        input_ref=None,
        status="running",
        started_at=time.time(),
    ) == "created"


def _event(run_id: str, event_id: str, event_type: str) -> dict[str, object]:
    return {
        "workflow_id": f"run-{run_id}",
        "segment_seq": 0,
        "event_id": event_id,
        "run_id": run_id,
        "type": event_type,
        "node": "root",
        "cid": "root-1",
        "ts": time.time(),
        "causes": [],
        "value_ref": None,
        "shape": None,
        "cost": None,
        "error": None,
        "attrs": {},
    }


def test_client_health_runs_events_and_errors(server_factory) -> None:
    harness = server_factory()
    run_id = "client-run"
    _seed_run(harness.store, run_id)
    harness.store.insert_events(
        [_event(run_id, "planned", "Planned"), _event(run_id, "did", "Did")]
    )

    with TestClient(harness.app) as transport_client:
        client = JulepClient(api_key="alice-token", client=transport_client)
        assert client.health() == {"status": "ok"}
        assert client.list_runs()["items"][0]["run_id"] == run_id
        assert client.get_run(run_id)["status"] == "running"
        assert [row["event_id"] for row in client.read_events(run_id)["items"]] == [
            "planned",
            "did",
        ]
        events = client.projection_events(run_id)
        assert all(isinstance(event, ProjectionEvent) for event in events)
        assert events[1].event_id == "did"
        assert events[1].type is EventType.DID
        assert events[1].cid == "root-1"

        with pytest.raises(JulepClientError) as caught:
            client.get_run("missing")
        assert caught.value.status_code == 404


def test_start_run_requires_idempotency_or_run_id() -> None:
    client = JulepClient(client=TestClient(lambda scope, receive, send: None))
    with pytest.raises(ValueError, match="idempotency_key or run_id"):
        client.start_run(pipeline="summary")


def test_async_client_keeps_the_sync_public_method_surface() -> None:
    sync_methods = {
        name
        for name, value in vars(JulepClient).items()
        if not name.startswith("_") and callable(value)
    }
    async_methods = {
        name
        for name, value in vars(AsyncJulepClient).items()
        if not name.startswith("_") and callable(value)
    }

    assert async_methods - {"aclose"} == sync_methods


def test_publish_release_registers_manifest_as_admin(server_factory) -> None:
    from .conftest import make_release

    harness = server_factory()
    release = make_release()
    with TestClient(harness.app) as transport_client:
        client = JulepClient(api_key="admin-token", client=transport_client)
        row = client.publish_release(release.manifest_bytes)
        assert row["release_hash"] == release.release_hash
        assert harness.artifacts.has(release.release_hash.removeprefix("sha256:"))


def test_publish_release_requires_admin_key(server_factory) -> None:
    from .conftest import make_release

    harness = server_factory()
    release = make_release()
    with TestClient(harness.app) as transport_client:
        client = JulepClient(api_key="alice-token", client=transport_client)
        with pytest.raises(JulepClientError) as caught:
            client.publish_release(release.manifest_bytes)
        assert caught.value.status_code == 403


def test_sync_run_and_wait_submits_polls_and_unwraps_result() -> None:
    requests: list[httpx.Request] = []
    results = [
        httpx.Response(202, json={"run": {"run_id": "run-1", "status": "running"}}),
        httpx.Response(
            200,
            json={
                "run": {"run_id": "run-1", "status": "completed"},
                "result": {"summary": "done"},
            },
        ),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(201, json={"run_id": "run-1", "status": "accepted"})
        return results.pop(0)

    transport = httpx.Client(
        base_url="https://julep.invalid",
        transport=httpx.MockTransport(handler),
    )
    client = JulepClient(api_key="secret", client=transport)

    value = client.run_and_wait(
        pipeline="summary",
        input={"value": 1},
        release="sha256:" + "a" * 64,
        idempotency_key="request-1",
        deadline_s=5,
        poll_wait_s=2,
    )

    assert value == {"summary": "done"}
    assert [request.url.path for request in requests] == [
        "/v1/runs",
        "/v1/runs/run-1/result",
        "/v1/runs/run-1/result",
    ]
    assert all(
        0 < float(request.url.params["wait_s"]) <= 2 for request in requests[1:]
    )
    assert requests[0].headers["Idempotency-Key"] == "request-1"
    assert requests[0].headers["Authorization"] == "Bearer secret"


def test_sync_start_and_wait_raises_typed_terminal_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(201, json={"run_id": "run-failed"})
        return httpx.Response(
            200,
            json={
                "run": {
                    "run_id": "run-failed",
                    "status": "failed",
                    "error": "provider unavailable",
                },
                "result": None,
            },
        )

    transport = httpx.Client(
        base_url="https://julep.invalid",
        transport=httpx.MockTransport(handler),
    )
    client = JulepClient(client=transport)

    with pytest.raises(JulepRunFailed) as caught:
        client.start_and_wait(
            pipeline="summary",
            idempotency_key="failed",
            deadline_s=5,
        )

    assert caught.value.run_id == "run-failed"
    assert caught.value.status == "failed"
    assert caught.value.error == "provider unavailable"


@pytest.mark.parametrize(
    ("status", "terminal_detail"),
    [
        ("canceled", None),
        ("terminated", {"reason": "operator request"}),
        ("start_failed", "Temporal unavailable"),
    ],
)
def test_sync_wait_covers_every_non_failure_terminal_status(
    status: str,
    terminal_detail: object,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "run": {
                    "run_id": "run-terminal",
                    "status": status,
                    "detail": terminal_detail,
                },
                "result": None,
            },
        )

    transport = httpx.Client(
        base_url="https://julep.invalid",
        transport=httpx.MockTransport(handler),
    )
    client = JulepClient(client=transport)

    with pytest.raises(JulepRunFailed) as caught:
        client.wait_for_run("run-terminal", deadline_s=5)

    assert caught.value.run_id == "run-terminal"
    assert caught.value.status == status
    assert caught.value.detail == terminal_detail


def test_sync_wait_deadline_expires_before_an_unbounded_poll() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(201, json={"run_id": "run-slow"})

    transport = httpx.Client(
        base_url="https://julep.invalid",
        transport=httpx.MockTransport(handler),
    )
    client = JulepClient(client=transport)

    with pytest.raises(JulepRunTimeout) as caught:
        client.run_and_wait(
            pipeline="summary",
            idempotency_key="slow",
            deadline_s=0,
        )

    assert caught.value.run_id == "run-slow"
    assert caught.value.deadline_s == 0


def test_async_start_and_wait_submits_polls_and_unwraps_result() -> None:
    requests: list[httpx.Request] = []
    results = [
        httpx.Response(202, json={"run": {"run_id": "run-a", "status": "accepted"}}),
        httpx.Response(
            200,
            json={
                "run": {"run_id": "run-a", "status": "completed"},
                "result": ["done"],
            },
        ),
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(201, json={"run_id": "run-a"})
        return results.pop(0)

    transport = httpx.AsyncClient(
        base_url="https://julep.invalid",
        transport=httpx.MockTransport(handler),
    )
    client = AsyncJulepClient(api_key="secret", client=transport)

    async def exercise() -> object:
        try:
            return await client.start_and_wait(
                pipeline="summary",
                idempotency_key="async-request",
                deadline_s=5,
                poll_wait_s=1,
            )
        finally:
            await transport.aclose()

    value = asyncio.run(exercise())

    assert value == ["done"]
    assert len(requests) == 3
    assert all(
        0 < float(request.url.params["wait_s"]) <= 1 for request in requests[1:]
    )


def test_async_run_and_wait_honors_deadline() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return httpx.Response(201, json={"run_id": "run-async-slow"})

    transport = httpx.AsyncClient(
        base_url="https://julep.invalid",
        transport=httpx.MockTransport(handler),
    )
    client = AsyncJulepClient(client=transport)

    async def exercise() -> None:
        try:
            await client.run_and_wait(
                pipeline="summary",
                idempotency_key="async-slow",
                deadline_s=0,
            )
        finally:
            await transport.aclose()

    with pytest.raises(JulepRunTimeout) as caught:
        asyncio.run(exercise())

    assert caught.value.run_id == "run-async-slow"


def test_run_and_wait_executes_against_local_api_end_to_end(tmp_path) -> None:
    """The adoption client and zero-daemon API compose without consumer glue."""

    from julep import deploy, ident
    from julep.app_deploy import ApplicationRelease, PipelineRelease
    from julep.freeze import McpSnapshot

    app = server.create_local_app(project_root=tmp_path)
    deployment = deploy(ident(), McpSnapshot())
    release = ApplicationRelease(
        application="client-local-acceptance",
        application_artifact_hash="sha256:" + "a" * 64,
        worker_image="registry.invalid/client-local@sha256:" + "b" * 64,
        pipelines=(
            PipelineRelease(
                name="summary",
                lane="local",
                artifact_hash=deployment.artifact_hash,
                flow_json=deployment.flow_json,
                manifest_json=deployment.manifest_json,
                pinned_pures={},
                bundle_ref=None,
                eval_packages=(),
                max_call_limits={},
                mcp_preflight_policy="pin",
            ),
        ),
    )
    payload = {"question": "can the client execute this locally?"}

    with TestClient(app) as transport_client:
        client = JulepClient(api_key="local-dev", client=transport_client)
        published = client.publish_release(release.manifest_bytes)
        assert published["release_hash"] == release.release_hash

        first = client.run_and_wait(
            pipeline="summary",
            input=payload,
            release=release.release_hash,
            idempotency_key="client-local-acceptance",
            deadline_s=2,
            poll_wait_s=0.1,
        )
        retry = client.run_and_wait(
            pipeline="summary",
            input=payload,
            release=release.release_hash,
            idempotency_key="client-local-acceptance",
            deadline_s=2,
            poll_wait_s=0.1,
        )

        assert first == payload
        assert retry == payload
        runs = client.list_runs()["items"]
        assert len(runs) == 1
        assert runs[0]["pipeline"] == "summary"
