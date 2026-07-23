from __future__ import annotations

from fastapi.routing import APIRoute
from starlette.testclient import TestClient

from julep.server.auth import require_admin, require_client, require_worker

from .conftest import ADMIN_HEADERS, ALICE_HEADERS, WORKER_HEADERS


def test_secret_api_is_write_only_role_scoped_and_rotates(server_factory) -> None:
    harness = server_factory()
    with TestClient(harness.app) as client:
        created = client.put(
            "/v1/secrets/tracker-token",
            json={"value": "first-value"},
            headers=ADMIN_HEADERS,
        )
        assert created.status_code == 200, created.text
        assert created.json()["generation"] == 1
        assert "value" not in created.json()
        assert "ciphertext" not in created.json()

        assert client.get("/v1/secrets", headers=ALICE_HEADERS).status_code == 403
        listed = client.get("/v1/secrets", headers=ADMIN_HEADERS)
        assert [item["name"] for item in listed.json()["items"]] == [
            "tracker-token"
        ]
        assert "value" not in listed.text
        assert "first-value" not in listed.text

        assert (
            client.get(
                "/v1/secrets/tracker-token/value", headers=ADMIN_HEADERS
            ).status_code
            == 403
        )
        fetched = client.get(
            "/v1/secrets/tracker-token/value", headers=WORKER_HEADERS
        )
        assert fetched.status_code == 200
        assert fetched.headers["cache-control"] == "no-store"
        assert fetched.json() == {"value": "first-value", "generation": 1}

        rotated = client.put(
            "/v1/secrets/tracker-token",
            json={"value": "second-value"},
            headers=ADMIN_HEADERS,
        )
        assert rotated.json()["generation"] == 2
        assert client.get(
            "/v1/secrets/tracker-token/value", headers=WORKER_HEADERS
        ).json() == {"value": "second-value", "generation": 2}


def test_secret_api_allowlist_archive_delete_and_name_validation(server_factory) -> None:
    harness = server_factory()
    with TestClient(harness.app) as client:
        assert client.put(
            "/v1/secrets/not-allowed",
            json={"value": "hidden"},
            headers=ADMIN_HEADERS,
        ).status_code == 200
        assert (
            client.get(
                "/v1/secrets/not-allowed/value", headers=WORKER_HEADERS
            ).status_code
            == 403
        )
        assert client.put(
            "/v1/secrets/Uppercase",
            json={"value": "hidden"},
            headers=ADMIN_HEADERS,
        ).status_code == 400

        assert client.put(
            "/v1/secrets/other-token",
            json={"value": "to-archive"},
            headers=ADMIN_HEADERS,
        ).status_code == 200
        archived = client.post(
            "/v1/secrets/other-token/archive", headers=ADMIN_HEADERS
        )
        assert archived.status_code == 200
        assert archived.json()["archived_at"] is not None
        assert client.get(
            "/v1/secrets/other-token/value", headers=WORKER_HEADERS
        ).status_code == 410

        deleted = client.delete(
            "/v1/secrets/other-token", headers=ADMIN_HEADERS
        )
        assert deleted.status_code == 204
        assert client.delete(
            "/v1/secrets/other-token", headers=ADMIN_HEADERS
        ).status_code == 404


def test_worker_role_is_rejected_from_every_non_secret_route(server_factory) -> None:
    harness = server_factory()
    with TestClient(harness.app) as client:
        # One representative endpoint from every authenticated router. Route
        # dependencies are all require_client/require_admin after the audit.
        paths = (
            ("GET", "/v1/ready"),
            ("HEAD", "/v1/artifacts/" + "0" * 64),
            ("GET", "/v1/releases"),
            ("GET", "/v1/deployments"),
            ("GET", "/v1/runs"),
        )
        for method, path in paths:
            response = client.request(method, path, headers=WORKER_HEADERS)
            assert response.status_code == 403, (method, path, response.text)

        assert client.get("/v1/health", headers=WORKER_HEADERS).status_code == 200


def test_every_authenticated_route_declares_an_explicit_role(server_factory) -> None:
    harness = server_factory()
    role_dependencies = {require_client, require_worker, require_admin}
    for route in harness.app.routes:
        if not isinstance(route, APIRoute) or route.path == "/v1/health":
            continue
        declared = {
            dependency.call for dependency in route.dependant.dependencies
        }
        assert declared & role_dependencies, (route.path, route.methods)
        if require_worker in declared:
            assert route.path == "/v1/secrets/{name}/value"
