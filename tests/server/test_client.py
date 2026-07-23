from __future__ import annotations

import asyncio
import time

import httpx
import pytest
from starlette.testclient import TestClient

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
