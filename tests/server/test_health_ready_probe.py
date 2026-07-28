from __future__ import annotations

from starlette.testclient import TestClient

from julep.server.routes import health as health_routes

from .conftest import ALICE_HEADERS


def test_unauthenticated_readiness_is_hidden_without_flag(server_factory, monkeypatch) -> None:
    async def unexpected_checks(request) -> dict[str, str]:
        raise AssertionError("dependency checks must not run")

    monkeypatch.setattr(health_routes, "_dependency_checks", unexpected_checks)
    harness = server_factory()

    with TestClient(harness.app) as client:
        response = client.get("/v1/health/ready")

    assert response.status_code == 404
    assert response.json() == {"detail": "not found"}


def test_unauthenticated_readiness_checks_dependencies_when_enabled(
    server_factory,
) -> None:
    harness = server_factory(unauthenticated_ready=True)

    with TestClient(harness.app) as client:
        ready = client.get("/v1/health/ready")
        assert ready.status_code == 200
        assert ready.json() == {
            "status": "ready",
            "checks": {
                "store": "ok",
                "artifacts": "ok",
                "temporal": "ok",
            },
        }
        authenticated_ready = client.get("/v1/ready", headers=ALICE_HEADERS)
        assert authenticated_ready.status_code == ready.status_code
        assert authenticated_ready.content == ready.content

        harness.gateway.is_ready = False
        unavailable = client.get("/v1/health/ready")
        assert unavailable.status_code == 503
        assert unavailable.json()["checks"]["temporal"].startswith("error:")

        assert client.get("/v1/ready").status_code == 401
