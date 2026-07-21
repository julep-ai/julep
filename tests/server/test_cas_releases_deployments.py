from __future__ import annotations

import hashlib
import json

from starlette.testclient import TestClient

from julep.app_deploy import LaneApplyResult

from .conftest import ADMIN_HEADERS, ALICE_HEADERS, make_release


def _publish(client: TestClient, release) -> dict:
    response = client.post(
        "/v1/releases",
        content=release.manifest_bytes,
        headers={**ADMIN_HEADERS, "Content-Type": "application/json"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_cas_upload_verifies_digest_and_head(server_factory) -> None:
    harness = server_factory()
    body = b"release blob"
    digest = hashlib.sha256(body).hexdigest()
    headers = {**ADMIN_HEADERS, "Content-Type": "application/octet-stream"}

    with TestClient(harness.app) as client:
        mismatch = client.put(f"/v1/cas/{'0' * 64}", content=body, headers=headers)
        assert mismatch.status_code == 400
        assert client.head(f"/v1/cas/{digest}", headers=ALICE_HEADERS).status_code == 404
        assert client.put(f"/v1/cas/{digest}", content=body, headers=headers).status_code == 201
        assert client.put(f"/v1/cas/{digest}", content=body, headers=headers).status_code == 200
        assert client.head(f"/v1/cas/{digest}", headers=ALICE_HEADERS).status_code == 200
        assert harness.cas.get(digest) == body


def test_release_validation_missing_blobs_and_recomputed_hash(server_factory) -> None:
    harness = server_factory()
    valid = make_release()
    schema_one = json.loads(valid.manifest_bytes)
    schema_one["schemaVersion"] = 1

    missing = make_release(
        bundle_ref=[
            {
                "bundleHash": "b" * 64,
                "signatureDigest": "c" * 64,
            }
        ]
    )
    with TestClient(harness.app) as client:
        old = client.post("/v1/releases", json=schema_one, headers=ADMIN_HEADERS)
        assert old.status_code == 400
        assert "version 2 is required" in old.json()["detail"]

        missing_response = client.post(
            "/v1/releases",
            content=missing.manifest_bytes,
            headers={**ADMIN_HEADERS, "Content-Type": "application/json"},
        )
        assert missing_response.status_code == 409
        assert missing_response.json()["detail"]["digests"] == ["b" * 64, "c" * 64]

        payload = json.loads(valid.manifest_bytes)
        payload["releaseHash"] = "sha256:" + "f" * 64
        published = client.post("/v1/releases", json=payload, headers=ADMIN_HEADERS)
        assert published.status_code == 201
        row = published.json()
        assert row["release_hash"] == valid.release_hash
        assert harness.cas.has(valid.release_hash.removeprefix("sha256:"))

        fetched = client.get(
            f"/v1/releases/{valid.release_hash}", headers=ALICE_HEADERS
        )
        assert fetched.status_code == 200
        assert fetched.json()["manifest"] == json.loads(valid.manifest_bytes)
        listed = client.get("/v1/releases?limit=1", headers=ALICE_HEADERS).json()
        assert [item["release_hash"] for item in listed["items"]] == [valid.release_hash]


def test_deployment_activation_and_rollback(server_factory) -> None:
    harness = server_factory()
    first = make_release(marker="a")
    second = make_release(marker="b")

    with TestClient(harness.app) as client:
        _publish(client, first)
        _publish(client, second)

        initial = client.post(
            "/v1/deployments",
            json={"lane": "summary", "release": first.release_hash},
            headers=ADMIN_HEADERS,
        )
        assert initial.status_code == 200
        assert initial.json()["release_hash"] == first.release_hash
        assert initial.json()["reconcile"]["status"] == "external"

        promoted = client.post(
            "/v1/deployments",
            json={"lane": "summary", "release": second.release_hash},
            headers=ADMIN_HEADERS,
        )
        assert promoted.json()["release_hash"] == second.release_hash

        rolled_back = client.post(
            "/v1/deployments",
            json={"lane": "summary", "release": first.release_hash},
            headers=ADMIN_HEADERS,
        )
        assert rolled_back.json()["release_hash"] == first.release_hash
        deployments = client.get("/v1/deployments", headers=ALICE_HEADERS).json()
        assert deployments["items"][0]["release_hash"] == first.release_hash


def test_deployment_runs_configured_lane_reconciler(server_factory) -> None:
    calls: list[tuple[str, str]] = []

    class Reconciler:
        def reconcile(self, release, lane: str, *, task_queue: str) -> LaneApplyResult:
            calls.append((lane, task_queue))
            return LaneApplyResult(
                lane=lane,
                release_name="memory-summary",
                task_queue=task_queue,
            )

    harness = server_factory(
        reconciler=Reconciler(),
        queue_by_lane={"summary": "configured-summary"},
    )
    release = make_release()
    with TestClient(harness.app) as client:
        _publish(client, release)
        response = client.post(
            "/v1/deployments",
            json={"lane": "summary", "release": release.release_hash},
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 200
    assert calls == [("summary", "configured-summary")]
    assert response.json()["reconcile"] == {
        "status": "ready",
        "release_name": "memory-summary",
        "task_queue": "configured-summary",
    }
