from __future__ import annotations

import asyncio
import base64
import json
import threading
import time
from urllib.parse import quote

from starlette.testclient import TestClient

from julep.execution.projection_store import InMemoryExecutionStore
from julep.projection import value_ref
from julep.server.routes.runs import reconcile_runs_once

from .conftest import (
    ADMIN_HEADERS,
    ALICE_HEADERS,
    BOB_HEADERS,
    FakeTemporalGateway,
    make_release,
)


def _publish(client: TestClient, release) -> None:
    response = client.post(
        "/v1/releases",
        content=release.manifest_bytes,
        headers={**ADMIN_HEADERS, "Content-Type": "application/json"},
    )
    assert response.status_code == 201, response.text


def _start(client: TestClient, release_hash: str, *, key: str = "request-1"):
    return client.post(
        "/v1/runs",
        json={
            "release": release_hash,
            "pipeline": "summary",
            "input": {"question": "hello"},
            "principal": {"tenant": "one"},
            "queueLanes": {"summary": "summary-queue"},
        },
        headers={**ALICE_HEADERS, "Idempotency-Key": key},
    )


def _event(
    run_id: str,
    workflow_id: str,
    event_id: str,
    *,
    value_ref_: str | None = None,
    terminal: bool = False,
) -> dict:
    return {
        "workflow_id": workflow_id,
        "segment_seq": 0,
        "event_id": event_id,
        "run_id": run_id,
        "type": "DID",
        "node": "root",
        "cid": event_id,
        "ts": time.time(),
        "causes": [],
        "value_ref": value_ref_,
        "shape": None,
        "cost": None,
        "error": None,
        "attrs": {"terminal": True, "status": "completed"} if terminal else {},
    }


def _finalize(store, run_id: str, workflow_id: str, result: object) -> None:
    result_ref = value_ref(result)
    store.finalize_run(
        run_id=run_id,
        workflow_id=workflow_id,
        segment_seq=0,
        status="completed",
        terminal_event=_event(
            run_id,
            workflow_id,
            "terminal",
            value_ref_=result_ref,
            terminal=True,
        ),
        result_payload=result,
        result_byte_len=len(json.dumps(result, separators=(",", ":")).encode()),
        result_oversize=False,
        error=None,
        finished_at=time.time(),
    )


def test_run_submission_is_idempotent_and_starts_once(server_factory) -> None:
    harness = server_factory()
    release = make_release()
    with TestClient(harness.app) as client:
        _publish(client, release)
        first = _start(client, release.release_hash)
        assert first.status_code == 201, first.text
        row = first.json()
        assert row["status"] == "accepted"
        assert row["principal"] == {"key": "alice", "tenant": "one"}
        assert row["temporal_run_id"] == f"temporal-{row['run_id']}"
        assert len(harness.gateway.starts) == 1
        assert harness.gateway.starts[0]["workflow_id"] == f"run-{row['run_id']}"
        assert harness.gateway.starts[0]["queue_lanes"] == {"summary": "summary-queue"}

        duplicate = _start(client, release.release_hash)
        assert duplicate.status_code == 200
        assert duplicate.json() == row
        assert len(harness.gateway.starts) == 1
        listed = client.get("/v1/runs", headers=ALICE_HEADERS).json()
        assert [item["run_id"] for item in listed["items"]] == [row["run_id"]]

        collision = client.post(
            "/v1/runs",
            json={"release": release.release_hash, "pipeline": "summary"},
            headers={**BOB_HEADERS, "Idempotency-Key": "request-1"},
        )
        assert collision.status_code == 409
        assert len(harness.gateway.starts) == 1


def test_run_submission_validation_and_start_failure(server_factory) -> None:
    harness = server_factory()
    release = make_release()
    with TestClient(harness.app) as client:
        _publish(client, release)
        assert client.post(
            "/v1/runs",
            json={"release": release.release_hash, "pipeline": "summary"},
            headers=ALICE_HEADERS,
        ).status_code == 400

        collision = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "runId": "explicit",
                "principal": {"key": "bob"},
            },
            headers=ALICE_HEADERS,
        )
        assert collision.status_code == 400

        harness.gateway.fail_start = True
        failed = _start(client, release.release_hash, key="will-fail")
        assert failed.status_code == 502
        stored = harness.store.get_run_by_idempotency_key("will-fail")
        assert stored is not None
        assert stored["status"] == "start_failed"
        result = client.get(
            f"/v1/runs/{stored['run_id']}/result", headers=ALICE_HEADERS
        )
        assert result.status_code == 200
        assert result.json()["run"]["status"] == "start_failed"


def test_run_secrets_are_forwarded_but_never_persisted(server_factory) -> None:
    harness = server_factory()
    release = make_release()
    submitted = "tenant token:that/must-not-persist"
    encoded = base64.b64encode(submitted.encode()).decode()
    urlencoded = quote(submitted, safe="")
    run_input = {
        "raw": submitted,
        "encoded": encoded,
        "urlencoded": urlencoded,
        f"raw-key:{submitted}": "one",
        f"encoded-key:{encoded}": "two",
        f"url-key:{urlencoded}": "three",
    }

    with TestClient(harness.app) as client:
        _publish(client, release)
        response = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "input": run_input,
                "secrets": {"tracker-token": submitted},
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "run-secret"},
        )

    assert response.status_code == 201, response.text
    row = response.json()
    assert harness.gateway.starts[0]["secrets"] == {"tracker-token": submitted}
    assert harness.gateway.starts[0]["input"] == run_input
    stored_input = harness.store.get_value(row["input_ref"])
    assert stored_input is not None
    serialized = json.dumps(stored_input, sort_keys=True)
    assert submitted not in serialized
    assert encoded not in serialized
    assert urlencoded not in serialized
    assert submitted not in json.dumps(row, sort_keys=True)


def test_run_secret_submission_validates_names_values_and_encryption(server_factory) -> None:
    release = make_release()
    harness = server_factory()
    with TestClient(harness.app) as client:
        _publish(client, release)
        invalid_name = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "secrets": {"Not Allowed": "value"},
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "invalid-name"},
        )
        empty_value = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "secrets": {"tracker-token": ""},
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "empty-value"},
        )
        too_many = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "secrets": {f"secret-{index}": "x" for index in range(33)},
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "too-many-secrets"},
        )
        too_large = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "secrets": {"tracker-token": "x" * (16 * 1024 + 1)},
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "too-large-secret"},
        )
        too_large_total = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "secrets": {
                    f"secret-{index}": "x" * (16 * 1024)
                    for index in range(4)
                },
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "too-large-total"},
        )

    assert invalid_name.status_code == 400
    assert empty_value.status_code == 400
    assert too_many.status_code == 400
    assert too_large.status_code == 400
    assert too_large_total.status_code == 400

    plaintext = server_factory(payload_encryption_required=False)
    with TestClient(plaintext.app) as client:
        _publish(client, release)
        response = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "secrets": {"tracker-token": "value"},
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "plaintext"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "run secrets require Temporal payload encryption"
    assert plaintext.gateway.starts == []


def test_mcp_preflight_override_requires_admin(server_factory) -> None:
    harness = server_factory()
    release = make_release()
    payload = {
        "release": release.release_hash,
        "pipeline": "summary",
        "mcpPreflight": "off",
    }
    with TestClient(harness.app) as client:
        _publish(client, release)
        denied = client.post(
            "/v1/runs",
            json=payload,
            headers={**ALICE_HEADERS, "Idempotency-Key": "client-override"},
        )
        accepted = client.post(
            "/v1/runs",
            json=payload,
            headers={**ADMIN_HEADERS, "Idempotency-Key": "admin-override"},
        )

    assert denied.status_code == 403
    assert accepted.status_code == 201
    assert harness.gateway.starts[0]["pipeline"].mcp_preflight_policy == "off"


def test_old_release_rejects_run_secrets_instead_of_ignoring_them(server_factory) -> None:
    harness = server_factory()
    release = make_release(mcp_preflight_policy=None)
    with TestClient(harness.app) as client:
        _publish(client, release)
        response = client.post(
            "/v1/runs",
            json={
                "release": release.release_hash,
                "pipeline": "summary",
                "secrets": {"tracker-token": "value"},
            },
            headers={**ALICE_HEADERS, "Idempotency-Key": "old-release-secret"},
        )

    assert response.status_code == 400
    assert "predates run-secret" in response.json()["detail"]
    assert harness.gateway.starts == []


def test_ambiguous_start_is_left_submitting_for_reconciliation(server_factory) -> None:
    harness = server_factory()
    release = make_release()
    harness.gateway.ambiguous_start = True

    with TestClient(harness.app) as client:
        _publish(client, release)
        failed = _start(client, release.release_hash, key="ambiguous-start")

    assert failed.status_code == 502
    assert failed.json()["detail"] == (
        "Temporal workflow start is unconfirmed; "
        "run left submitting for reconciliation"
    )
    stored = harness.store.get_run_by_idempotency_key("ambiguous-start")
    assert stored is not None
    assert stored["status"] == "submitting"

    harness.gateway.descriptions[stored["workflow_id"]] = "running"
    asyncio.run(reconcile_runs_once(harness.store, harness.gateway))

    reconciled = harness.store.get_run(stored["run_id"])
    assert reconciled is not None
    assert reconciled["status"] == "accepted"


def test_projection_can_win_start_response_race_without_losing_temporal_id(
    server_factory,
) -> None:
    store = InMemoryExecutionStore()

    class EagerGateway(FakeTemporalGateway):
        async def start_flow(self, pipeline, **kwargs):
            store.insert_events(
                [
                    _event(
                        kwargs["run_id"],
                        kwargs["workflow_id"],
                        "eager-event",
                    )
                ]
            )
            return await super().start_flow(pipeline, **kwargs)

    gateway = EagerGateway()
    harness = server_factory(store=store, gateway=gateway)
    release = make_release()
    with TestClient(harness.app) as client:
        _publish(client, release)
        response = _start(client, release.release_hash, key="eager")

    assert response.status_code == 201
    row = response.json()
    assert row["status"] == "running"
    assert row["temporal_run_id"] == f"temporal-{row['run_id']}"


def test_terminal_write_can_win_start_response_without_status_regression(
    server_factory,
) -> None:
    store = InMemoryExecutionStore()

    class FinishedGateway(FakeTemporalGateway):
        async def start_flow(self, pipeline, **kwargs):
            _finalize(
                store,
                kwargs["run_id"],
                kwargs["workflow_id"],
                {"finished": True},
            )
            return await super().start_flow(pipeline, **kwargs)

    gateway = FinishedGateway()
    harness = server_factory(store=store, gateway=gateway)
    release = make_release()
    with TestClient(harness.app) as client:
        _publish(client, release)
        response = _start(client, release.release_hash, key="fast-finish")

    assert response.status_code == 201
    row = response.json()
    assert row["status"] == "completed"
    assert row["temporal_run_id"] == f"temporal-{row['run_id']}"


def test_result_events_values_controls_gates_and_signal(server_factory) -> None:
    harness = server_factory()
    release = make_release()
    harness.gateway.query_result = [{"cid": "approval"}]
    with TestClient(harness.app) as client:
        _publish(client, release)
        started = _start(client, release.release_hash, key="result-run").json()
        run_id = started["run_id"]
        workflow_id = started["workflow_id"]

        visible_ref = "val:visible"
        oversize_ref = "val:oversize"
        unrelated_ref = "val:unrelated"
        harness.store.put_value(visible_ref, {"visible": True}, 16, False)
        harness.store.put_value(oversize_ref, None, 100_000, True)
        harness.store.put_value(unrelated_ref, {"secret": True}, 15, False)
        harness.store.insert_events(
            [
                _event(run_id, workflow_id, "one", value_ref_=visible_ref),
                _event(run_id, workflow_id, "two", value_ref_=oversize_ref),
            ]
        )

        timer = threading.Timer(
            0.05,
            _finalize,
            args=(harness.store, run_id, workflow_id, {"answer": 42}),
        )
        timer.start()
        try:
            result = client.get(
                f"/v1/runs/{run_id}/result?wait_s=1", headers=ALICE_HEADERS
            )
        finally:
            timer.join(timeout=1)
        assert result.status_code == 200
        assert result.json()["result"] == {"answer": 42}

        events = client.get(
            f"/v1/runs/{run_id}/events?limit=2",
            headers={**ALICE_HEADERS, "Accept": "application/json"},
        ).json()
        assert [item["event_id"] for item in events["items"]] == ["one", "two"]
        assert events["next_cursor"] == str(events["items"][-1]["seq"])
        resumed = client.get(
            f"/v1/runs/{run_id}/events",
            headers={
                **ALICE_HEADERS,
                "Accept": "application/json",
                "Last-Event-ID": events["next_cursor"],
            },
        ).json()
        assert [item["event_id"] for item in resumed["items"]] == ["terminal"]
        assert resumed["items"][0]["attrs"]["terminal"] is True

        assert client.get(
            f"/v1/runs/{run_id}/values/{visible_ref}", headers=ALICE_HEADERS
        ).json()["payload"] == {"visible": True}
        assert client.get(
            f"/v1/runs/{run_id}/values/{oversize_ref}", headers=ALICE_HEADERS
        ).status_code == 404
        assert client.get(
            f"/v1/runs/{run_id}/values/{unrelated_ref}", headers=ALICE_HEADERS
        ).status_code == 404

        gates = client.get(f"/v1/runs/{run_id}/gates", headers=ALICE_HEADERS)
        assert gates.json() == {"gates": [{"cid": "approval"}]}
        signal = client.post(
            f"/v1/runs/{run_id}/signals/human",
            json={"cid": "approval", "value": {"approved": True}},
            headers=ALICE_HEADERS,
        )
        assert signal.status_code == 200
        assert harness.gateway.signals == [
            (
                workflow_id,
                "submitHuman",
                {"cid": "approval", "value": {"approved": True}},
            )
        ]

        assert client.post(
            f"/v1/runs/{run_id}/cancel", headers=ALICE_HEADERS
        ).status_code == 200
        assert client.post(
            f"/v1/runs/{run_id}/terminate", headers=ALICE_HEADERS
        ).status_code == 200
        assert harness.gateway.canceled == [workflow_id]
        assert harness.gateway.terminated == [workflow_id]


def test_invalid_list_cursor_is_a_client_error(server_factory) -> None:
    harness = server_factory()
    with TestClient(harness.app) as client:
        assert client.get(
            "/v1/runs?cursor=not-base64", headers=ALICE_HEADERS
        ).status_code == 400
        assert client.get(
            "/v1/releases?cursor=not-base64", headers=ALICE_HEADERS
        ).status_code == 400
