from __future__ import annotations

from starlette.testclient import TestClient

from .conftest import ADMIN_HEADERS, ALICE_HEADERS


def _seed_run(store, run_id: str, owner: str, started_at: float) -> None:
    assert store.create_run(
        run_id=run_id,
        idempotency_key=f"idem-{run_id}",
        workflow_id=f"run-{run_id}",
        session_id=f"run-{run_id}",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": owner},
        input_ref=None,
        started_at=started_at,
    ) == "created"


def test_health_and_readiness_are_unauthenticated(server_factory) -> None:
    harness = server_factory()
    with TestClient(harness.app) as client:
        assert client.get("/v1/health").json() == {"status": "ok"}
        ready = client.get("/v1/ready")
        assert ready.status_code == 200
        assert ready.json()["checks"] == {
            "store": "ok",
            "cas": "ok",
            "temporal": "ok",
        }

        harness.gateway.is_ready = False
        unavailable = client.get("/v1/ready")
        assert unavailable.status_code == 503
        assert unavailable.json()["checks"]["temporal"].startswith("error:")


def test_authentication_and_admin_authorization(server_factory) -> None:
    harness = server_factory()
    digest = "0" * 64
    with TestClient(harness.app) as client:
        missing = client.get("/v1/runs")
        assert missing.status_code == 401
        assert missing.headers["www-authenticate"] == "Bearer"
        assert client.get(
            "/v1/runs", headers={"Authorization": "Bearer wrong"}
        ).status_code == 401
        assert client.put(
            f"/v1/cas/{digest}",
            content=b"not-the-digest",
            headers=ALICE_HEADERS,
        ).status_code == 403


def test_run_reads_and_lists_are_owner_scoped_with_admin_bypass(server_factory) -> None:
    harness = server_factory()
    _seed_run(harness.store, "alice-run", "alice", 1.0)
    _seed_run(harness.store, "bob-run", "bob", 2.0)

    with TestClient(harness.app) as client:
        assert client.get("/v1/runs/alice-run", headers=ALICE_HEADERS).status_code == 200
        assert client.get("/v1/runs/bob-run", headers=ALICE_HEADERS).status_code == 404
        alice_list = client.get("/v1/runs", headers=ALICE_HEADERS).json()
        assert [item["run_id"] for item in alice_list["items"]] == ["alice-run"]

        assert client.get("/v1/runs/bob-run", headers=ADMIN_HEADERS).status_code == 200
        admin_list = client.get("/v1/runs", headers=ADMIN_HEADERS).json()
        assert [item["run_id"] for item in admin_list["items"]] == [
            "bob-run",
            "alice-run",
        ]
