"""
Tests for HTTP middleware, specifically the usage_check_middleware
"""

import uuid
from unittest.mock import AsyncMock, patch

import asyncpg
import pytest
from agents_api.app import app
from agents_api.clients.pg import create_db_pool
from agents_api.env import free_tier_cost_limit
from agents_api.queries.developers.create_developer import create_developer
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel
from uuid_extensions import uuid7

# Fixtures are now defined in conftest.py and automatically available to tests


class TestPayload(BaseModel):
    """Test payload for POST/PUT handlers."""

    message: str


@pytest.fixture
def client():
    """Test client fixture that gets reset for each test."""
    client = TestClient(app)
    yield client


async def test_middleware_inactive_free_user_receives_forbidden_response(client):
    """Test that requests from inactive users are blocked with 403 Forbidden."""

    @app.get("/test-inactive-user")
    async def test_inactive_user():
        return {"status": "success"}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": False,
        "cost": 0.0,
        "developer_id": developer_id,
        "tags": [],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = client.get("/test-inactive-user", headers={"X-Developer-Id": developer_id})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text


def test_middleware_inactive_paid_user_receives_forbidden_response(client):
    """Test that requests from inactive paid users are blocked with 403 Forbidden."""

    @app.get("/test-inactive-paid-user")
    async def test_inactive_paid_user():
        return {"status": "success"}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": False,
        "cost": 0.0,
        "developer_id": developer_id,
        "tags": ["paid"],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = client.get(
            "/test-inactive-paid-user", headers={"X-Developer-Id": developer_id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text


def test_middleware_cost_limit_exceeded_all_requests_blocked_except_get(client):
    """Test that non-GET requests from users who exceeded cost limits are blocked with 403 Forbidden."""

    @app.get("/test-cost-limit/get")
    async def test_cost_limit_get():
        return {"status": "success", "method": "GET"}

    @app.post("/test-cost-limit/post")
    async def test_cost_limit_post(payload: TestPayload):
        return {"status": "success", "method": "POST", "message": payload.message}

    @app.put("/test-methods/put")
    async def test_methods_put(payload: TestPayload):
        return {"status": "success", "method": "PUT", "message": payload.message}

    @app.delete("/test-methods/delete")
    async def test_methods_delete():
        return {"status": "success", "method": "DELETE"}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 1.0,
        "developer_id": developer_id,
        "tags": [],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        post_response = client.post(
            "/test-cost-limit/post",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )
        assert post_response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in post_response.text
        assert "cost_limit_exceeded" in post_response.text
        put_response = client.put(
            "/test-methods/put",
            json={"message": "test update"},
            headers={"X-Developer-Id": developer_id},
        )
        assert put_response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in put_response.text
        assert "cost_limit_exceeded" in put_response.text
        delete_response = client.delete(
            "/test-methods/delete", headers={"X-Developer-Id": developer_id}
        )
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in delete_response.text
        assert "cost_limit_exceeded" in delete_response.text
        get_response = client.get(
            "/test-cost-limit/get", headers={"X-Developer-Id": developer_id}
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["method"] == "GET"


def test_middleware_paid_tag_bypasses_cost_limit_check(client):
    """Test that users with 'paid' tag can make non-GET requests even when over the cost limit."""

    @app.post("/test-paid/post")
    async def test_paid_post(payload: TestPayload):
        return {"status": "success", "method": "POST", "message": payload.message}

    @app.put("/test-paid-methods/put")
    async def test_paid_methods_put(payload: TestPayload):
        return {"status": "success", "method": "PUT", "message": payload.message}

    @app.delete("/test-paid-methods/delete")
    async def test_paid_methods_delete():
        return {"status": "success", "method": "DELETE"}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 10.0,
        "developer_id": developer_id,
        "tags": ["test", "paid", "other-tag"],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = client.post(
            "/test-paid/post",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["method"] == "POST"
        assert response.json()["message"] == "test"
        put_response = client.put(
            "/test-paid-methods/put",
            json={"message": "test update"},
            headers={"X-Developer-Id": developer_id},
        )
        assert put_response.status_code == status.HTTP_200_OK
        assert put_response.json()["method"] == "PUT"
        delete_response = client.delete(
            "/test-paid-methods/delete", headers={"X-Developer-Id": developer_id}
        )
        assert delete_response.status_code == status.HTTP_200_OK
        assert delete_response.json()["method"] == "DELETE"


def test_middleware_get_request_with_cost_limit_exceeded_passes_through(client):
    """Test that GET requests from users who exceeded cost limits are allowed to proceed."""

    @app.get("/test-get-with-cost-limit")
    async def test_get_with_cost_limit():
        return {"status": "success", "method": "GET"}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 1.0,
        "developer_id": developer_id,
        "tags": [],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = client.get(
            "/test-get-with-cost-limit", headers={"X-Developer-Id": developer_id}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["method"] == "GET"


def test_middleware_cost_is_none_treats_as_exceeded_limit(client):
    """Test that non-GET requests with None cost value are treated as exceeding the limit."""

    @app.post("/test-none-cost")
    async def test_none_cost(payload: TestPayload):
        return {"status": "success", "method": "POST", "message": payload.message}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": None,
        "developer_id": developer_id,
        "tags": [],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = client.post(
            "/test-none-cost",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.text
        assert "cost_limit_exceeded" in response.text


def test_middleware_null_tags_field_handled_properly(client):
    """Test that users with null tags field are handled properly when over cost limit."""

    @app.post("/test-null-tags")
    async def test_null_tags(payload: TestPayload):
        return {"status": "success", "method": "POST", "message": payload.message}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 5.0,
        "developer_id": developer_id,
        "tags": None,
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = client.post(
            "/test-null-tags",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.text
        assert "cost_limit_exceeded" in response.text


def test_middleware_no_developer_id_header_passes_through(client):
    """Test that requests without a developer_id header are allowed to proceed."""

    @app.get("/test-no-developer-id")
    async def test_no_developer_id():
        return {"status": "success", "message": "no developer ID needed"}

    response = client.get("/test-no-developer-id")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "no developer ID needed"


def test_middleware_forbidden_if_user_is_not_found(client):
    """Test that requests resulting in NoDataFoundError return 403."""

    @app.get("/test-user-not-found")
    async def test_user_not_found():
        return {"status": "success", "message": "user found"}

    @app.get("/test-404-error")
    async def test_404_error():
        return {"status": "success", "message": "no 404 error"}

    developer_id = str(uuid.uuid4())
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(side_effect=asyncpg.NoDataFoundError())
    ):
        response = client.get("/test-user-not-found", headers={"X-Developer-Id": developer_id})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text
    http_404_error = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    with patch("agents_api.web.get_usage_cost", new=AsyncMock(side_effect=http_404_error)):
        response = client.get("/test-404-error", headers={"X-Developer-Id": developer_id})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text


def test_middleware_hand_over_all_the_http_errors_except_of_404(client):
    """Test that HTTP exceptions other than 404 return with correct status code."""

    @app.get("/test-500-error")
    async def test_500_error():
        return {"status": "success", "message": "no 500 error"}

    developer_id = str(uuid.uuid4())
    http_500_error = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
    )
    with patch("agents_api.web.get_usage_cost", new=AsyncMock(side_effect=http_500_error)):
        response = client.get("/test-500-error", headers={"X-Developer-Id": developer_id})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_middleware_invalid_uuid_returns_bad_request(client):
    """Test that requests with invalid UUID return 400 Bad Request."""

    @app.get("/test-invalid-uuid")
    async def test_invalid_uuid():
        return {"status": "success", "message": "valid UUID"}

    response = client.get("/test-invalid-uuid", headers={"X-Developer-Id": "invalid-uuid"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid developer ID" in response.text
    assert "invalid_developer_id" in response.text


def test_middleware_valid_user_passes_through(client):
    """Test that requests from valid users are allowed to proceed."""

    @app.get("/test-valid-user")
    async def test_valid_user():
        return {"status": "success", "message": "valid user"}

    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": 0.0,
        "developer_id": developer_id,
        "tags": [],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = client.get("/test-valid-user", headers={"X-Developer-Id": developer_id})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "valid user"


async def test_middleware_cant_create_session_when_cost_limit_is_reached(
    make_request, pg_dsn, test_agent
):
    """Test that creating a session fails with 403 when cost limit is reached."""
    pool = await create_db_pool(dsn=pg_dsn)
    developer_id = uuid7()
    email = f"test-{developer_id}@example.com"
    try:
        await create_developer(
            email=email,
            active=True,
            tags=[],
            settings={},
            developer_id=developer_id,
            connection_pool=pool,
        )
    finally:
        await pool.close()

    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 1.0,
        "developer_id": developer_id,
        "tags": [],
    }
    with patch(
        "agents_api.web.get_usage_cost", new=AsyncMock(return_value=mock_user_cost_data)
    ):
        response = make_request(
            method="POST",
            url="/sessions",
            json={"agent_id": str(test_agent.id)},
            headers={"X-Developer-Id": str(developer_id)},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.text
        assert "cost_limit_exceeded" in response.text


@pytest.mark.skip(reason="Test infrastructure issue with database pool initialization")
async def test_middleware_cant_delete_session_when_cost_limit_is_reached(
    make_request, test_developer, test_agent, test_session
):
    """Test that deleting a session fails with 403 when cost limit is reached."""
    # AIDEV-NOTE: Use existing fixtures to avoid state initialization issues
    developer_id = test_developer.id

    # AIDEV-NOTE: Mock responses need to return proper user_cost_data structure
    # First call returns cost below limit (for session creation/verification)
    # Second call returns cost above limit (for deletion attempt)
    mock_responses = [
        {
            "active": True,
            "cost": float(free_tier_cost_limit) - 0.5,
            "developer_id": str(developer_id),
            "tags": [],
        },
        {
            "active": True,
            "cost": float(free_tier_cost_limit) + 1.0,
            "developer_id": str(developer_id),
            "tags": [],
        },
    ]
    mock_get_usage_cost = AsyncMock()
    mock_get_usage_cost.side_effect = mock_responses

    # Use the existing test_session fixture instead of creating a new one
    with patch("agents_api.web.get_usage_cost", new=mock_get_usage_cost):
        # Verify we can access the session when under cost limit
        get_response = make_request(
            method="GET",
            url=f"/sessions/{test_session.id}",
            headers={"X-Developer-Id": str(developer_id)},
        )
        assert get_response.status_code == status.HTTP_200_OK

        # Now try to delete - should fail with cost limit exceeded
        delete_response = make_request(
            method="DELETE",
            url=f"/sessions/{test_session.id}",
            headers={"X-Developer-Id": str(developer_id)},
        )
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in delete_response.text
        assert "cost_limit_exceeded" in delete_response.text
