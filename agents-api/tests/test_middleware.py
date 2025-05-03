"""
Tests for HTTP middleware, specifically the usage_check_middleware
"""

import uuid
from unittest.mock import AsyncMock, patch

import asyncpg
from agents_api.app import app
from agents_api.env import free_tier_cost_limit
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel
from ward import fixture, test


class TestPayload(BaseModel):
    """Test payload for POST/PUT handlers."""

    message: str


@fixture
def client():
    """Test client fixture that gets reset for each test."""
    client = TestClient(app)
    yield client


@test("middleware: inactive free user receives forbidden response")
async def _(client=client):
    """Test that requests from inactive users are blocked with 403 Forbidden."""

    # Create a test handler
    @app.get("/test-inactive-user")
    async def test_inactive_user():
        return {"status": "success"}

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": False,
        "cost": 0.0,
        "developer_id": developer_id,
        "tags": [],
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make request with the developer ID header
        response = client.get("/test-inactive-user", headers={"X-Developer-Id": developer_id})

        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text


@test("middleware: inactive paid user receives forbidden response")
def _(client=client):
    """Test that requests from inactive paid users are blocked with 403 Forbidden."""

    # Create a test handler
    @app.get("/test-inactive-paid-user")
    async def test_inactive_paid_user():
        return {"status": "success"}

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": False,
        "cost": 0.0,
        "developer_id": developer_id,
        "tags": ["paid"],  # User has paid tag but is inactive
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make request with the developer ID header
        response = client.get(
            "/test-inactive-paid-user", headers={"X-Developer-Id": developer_id}
        )

        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text


@test("middleware: cost limit exceeded, all requests blocked except GET")
def _(client=client):
    """Test that non-GET requests from users who exceeded cost limits are blocked with 403 Forbidden."""

    # Create test handlers for different methods
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

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 1.0,  # Exceed the cost limit
        "developer_id": developer_id,
        "tags": [],  # No paid tag
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make a POST request that should be blocked
        post_response = client.post(
            "/test-cost-limit/post",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )

        # Verify POST response is 403 with correct message
        assert post_response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in post_response.text
        assert "cost_limit_exceeded" in post_response.text

        put_response = client.put(
            "/test-methods/put",
            json={"message": "test update"},
            headers={"X-Developer-Id": developer_id},
        )

        # Verify PUT response is 403 with correct message
        assert put_response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in put_response.text
        assert "cost_limit_exceeded" in put_response.text

        # Make a DELETE request that should be blocked
        delete_response = client.delete(
            "/test-methods/delete", headers={"X-Developer-Id": developer_id}
        )

        # Verify DELETE response is 403 with correct message
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in delete_response.text
        assert "cost_limit_exceeded" in delete_response.text

        # Make a GET request that should be allowed
        get_response = client.get(
            "/test-cost-limit/get", headers={"X-Developer-Id": developer_id}
        )

        # Verify GET response passes through
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["method"] == "GET"


@test("middleware: paid tag bypasses cost limit check")
def _(client=client):
    """Test that users with 'paid' tag can make non-GET requests even when over the cost limit."""

    # Create test handlers for different methods
    @app.post("/test-paid/post")
    async def test_paid_post(payload: TestPayload):
        return {"status": "success", "method": "POST", "message": payload.message}

    @app.put("/test-paid-methods/put")
    async def test_paid_methods_put(payload: TestPayload):
        return {"status": "success", "method": "PUT", "message": payload.message}

    @app.delete("/test-paid-methods/delete")
    async def test_paid_methods_delete():
        return {"status": "success", "method": "DELETE"}

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 10.0,  # Significantly exceed the cost limit
        "developer_id": developer_id,
        "tags": ["test", "paid", "other-tag"],  # Include "paid" tag
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make a POST request that should be allowed due to paid tag
        response = client.post(
            "/test-paid/post",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )

        # Verify the request was allowed
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["method"] == "POST"
        assert response.json()["message"] == "test"

        put_response = client.put(
            "/test-paid-methods/put",
            json={"message": "test update"},
            headers={"X-Developer-Id": developer_id},
        )

        # Verify the PUT request was allowed
        assert put_response.status_code == status.HTTP_200_OK
        assert put_response.json()["method"] == "PUT"

        # Make a DELETE request that should be allowed due to paid tag
        delete_response = client.delete(
            "/test-paid-methods/delete", headers={"X-Developer-Id": developer_id}
        )

        # Verify the DELETE request was allowed
        assert delete_response.status_code == status.HTTP_200_OK
        assert delete_response.json()["method"] == "DELETE"


@test("middleware: GET request with cost limit exceeded passes through")
def _(client=client):
    """Test that GET requests from users who exceeded cost limits are allowed to proceed."""

    # Create a test handler
    @app.get("/test-get-with-cost-limit")
    async def test_get_with_cost_limit():
        return {"status": "success", "method": "GET"}

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 1.0,  # Exceed the cost limit
        "developer_id": developer_id,
        "tags": [],
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make a GET request
        response = client.get(
            "/test-get-with-cost-limit", headers={"X-Developer-Id": developer_id}
        )

        # Verify the request was allowed
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["method"] == "GET"


@test("middleware: cost is None treats as exceeded limit")
def _(client=client):
    """Test that non-GET requests with None cost value are treated as exceeding the limit."""

    # Create a test handler
    @app.post("/test-none-cost")
    async def test_none_cost(payload: TestPayload):
        return {"status": "success", "method": "POST", "message": payload.message}

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": None,
        "developer_id": developer_id,
        "tags": [],
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make a POST request
        response = client.post(
            "/test-none-cost",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )

        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.text
        assert "cost_limit_exceeded" in response.text


@test("middleware: null tags field handled properly")
def _(client=client):
    """Test that users with null tags field are handled properly when over cost limit."""

    # Create a test handler
    @app.post("/test-null-tags")
    async def test_null_tags(payload: TestPayload):
        return {"status": "success", "method": "POST", "message": payload.message}

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 5.0,  # Exceed the cost limit
        "developer_id": developer_id,
        "tags": None,  # Null field
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make a POST request
        response = client.post(
            "/test-null-tags",
            json={"message": "test"},
            headers={"X-Developer-Id": developer_id},
        )

        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.text
        assert "cost_limit_exceeded" in response.text


@test("middleware: no developer_id header passes through")
def _(client=client):
    """Test that requests without a developer_id header are allowed to proceed."""

    # Create a test handler
    @app.get("/test-no-developer-id")
    async def test_no_developer_id():
        return {"status": "success", "message": "no developer ID needed"}

    # Make request with no developer ID header
    response = client.get("/test-no-developer-id")

    # Verify the request was allowed
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "no developer ID needed"


@test("middleware: forbidden, if user is not found")
def _(client=client):
    """Test that requests resulting in NoDataFoundError return 403."""

    # Create a test handler
    @app.get("/test-user-not-found")
    async def test_user_not_found():
        return {"status": "success", "message": "user found"}

    @app.get("/test-404-error")
    async def test_404_error():
        return {"status": "success", "message": "no 404 error"}

    # Create a random developer ID
    developer_id = str(uuid.uuid4())

    # Mock the get_user_cost function to raise NoDataFoundError
    with patch(
        "agents_api.web.get_user_cost", new=AsyncMock(side_effect=asyncpg.NoDataFoundError())
    ):
        # Make request with the developer ID header
        response = client.get("/test-user-not-found", headers={"X-Developer-Id": developer_id})

        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text

    # Mock the get_user_cost function to raise HTTPException with 404
    http_404_error = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    with patch("agents_api.web.get_user_cost", new=AsyncMock(side_effect=http_404_error)):
        # Make request with the developer ID header
        response = client.get("/test-404-error", headers={"X-Developer-Id": developer_id})

        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.text
        assert "invalid_user_account" in response.text


@test("middleware: hand over all the http errors except of 404")
def _(client=client):
    """Test that HTTP exceptions other than 404 return with correct status code."""

    # Create a test handler
    @app.get("/test-500-error")
    async def test_500_error():
        return {"status": "success", "message": "no 500 error"}

    # Create a random developer ID
    developer_id = str(uuid.uuid4())

    # Mock the get_user_cost function to raise HTTPException with 500
    http_500_error = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
    )
    with patch("agents_api.web.get_user_cost", new=AsyncMock(side_effect=http_500_error)):
        # Make request with the developer ID header
        response = client.get("/test-500-error", headers={"X-Developer-Id": developer_id})

        # Verify the response has the same status code as the exception
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@test("middleware: invalid uuid returns bad request")
def _(client=client):
    """Test that requests with invalid UUID return 400 Bad Request."""

    # Create a test handler
    @app.get("/test-invalid-uuid")
    async def test_invalid_uuid():
        return {"status": "success", "message": "valid UUID"}

    # Make request with invalid UUID
    response = client.get(
        "/test-invalid-uuid",
        headers={"X-Developer-Id": "invalid-uuid"},  # Invalid UUID
    )

    # Verify response is 400 with correct message
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid developer ID" in response.text
    assert "invalid_developer_id" in response.text


@test("middleware: valid user passes through")
def _(client=client):
    """Test that requests from valid users are allowed to proceed."""

    # Create a test handler
    @app.get("/test-valid-user")
    async def test_valid_user():
        return {"status": "success", "message": "valid user"}

    # Create test data
    developer_id = str(uuid.uuid4())
    mock_user_cost_data = {
        "active": True,
        "cost": 0.0,  # Below the limit
        "developer_id": developer_id,
        "tags": [],
    }

    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Make request with the developer ID header
        response = client.get("/test-valid-user", headers={"X-Developer-Id": developer_id})

        # Verify the request was allowed
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "valid user"
