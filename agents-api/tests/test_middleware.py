"""
Tests for HTTP middleware, specifically the usage_check_middleware
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from ward import test

from agents_api.env import free_tier_cost_limit
from agents_api.web import usage_check_middleware


@test("middleware: inactive free user receives forbidden response")
async def _():
    """Test that requests from inactive users are blocked with 403 Forbidden."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "GET"
    
    # Mock response from get_user_cost
    mock_user_cost_data = {
        "active": False,
        "cost": 0.0,
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": []
    }
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.body.decode()
        assert "invalid_user_account" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: inactive paid user receives forbidden response")
async def _():
    """Test that requests from inactive users are blocked with 403 Forbidden."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "GET"
    
    # Mock response from get_user_cost
    mock_user_cost_data = {
        "active": False,
        "cost": 0.0,
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": []
    }
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.body.decode()
        assert "invalid_user_account" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: cost limit exceeded, all requests blocked except GET")
async def _():
    """Test that non-GET requests from users who exceeded cost limits are blocked with 403 Forbidden."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "POST"  # Use a non-GET method
    
    # Mock response from get_user_cost with cost exceeding the limit
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 1.0,  # Exceed the cost limit
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": []
    }
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.body.decode()
        assert "cost_limit_exceeded" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: paid tag bypasses cost limit check")
async def _():
    """Test that users with 'paid' tag can make non-GET requests even when over the cost limit."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "POST"  # Use a non-GET method
    
    # Mock response from get_user_cost with cost exceeding the limit but with paid tag
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 10.0,  # Significantly exceed the cost limit
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": ["test", "paid", "other-tag"]  # Include "paid" tag
    }
    
    # Create a mock response for call_next
    mock_response = JSONResponse(content={"message": "Success"})
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock(return_value=mock_response)
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify call_next was called once - request went through despite cost limit
        mock_call_next.assert_called_once_with(mock_request)
        
        # Verify the original response is returned
        assert response == mock_response


@test("middleware: GET request with cost limit exceeded passes through")
async def _():
    """Test that GET requests from users who exceeded cost limits are allowed to proceed."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "GET"
    
    # Mock response from get_user_cost with cost exceeding the limit
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 1.0,  # Exceed the cost limit
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": []
    }
    
    # Create a mock response for call_next
    mock_response = JSONResponse(content={"message": "Success"})
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock(return_value=mock_response)
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify call_next was called once
        mock_call_next.assert_called_once_with(mock_request)
        
        # Verify the original response is returned
        assert response == mock_response


@test("middleware: cost is None treats as exceeded limit")
async def _():
    """Test that non-GET requests with None cost value are treated as exceeding the limit."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "POST"  # Use a non-GET method
    
    # Mock response from get_user_cost with None cost
    mock_user_cost_data = {
        "active": True,
        "cost": None,
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": []
    }
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.body.decode()
        assert "cost_limit_exceeded" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: non-list tags handled properly")
async def _():
    """Test that users with non-list tags field are handled properly when over cost limit."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "POST"  # Use a non-GET method
    
    # Mock response from get_user_cost with cost exceeding the limit and corrupted tags
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 5.0,  # Exceed the cost limit
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": "corrupted-string-instead-of-list"  # Not a list - should be handled gracefully
    }
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.body.decode()
        assert "cost_limit_exceeded" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: null tags field handled properly")
async def _():
    """Test that users with null tags field are handled properly."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "POST"  # Use a non-GET method
    
    # Mock response from get_user_cost with cost exceeding the limit and null tags
    mock_user_cost_data = {
        "active": True,
        "cost": float(free_tier_cost_limit) + 5.0,  # Exceed the cost limit
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": None  # Null field
    }
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cost limit exceeded" in response.body.decode()
        assert "cost_limit_exceeded" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: no developer_id header passes through")
async def _():
    """Test that requests without a developer_id header are allowed to proceed."""
    # Create mock request with no X-Developer-Id header
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({})
    
    # Create a mock response for call_next
    mock_response = JSONResponse(content={"message": "Success"})
    
    # Set up mock for call_next
    mock_call_next = AsyncMock(return_value=mock_response)
    
    # Call the middleware
    response = await usage_check_middleware(mock_request, mock_call_next)
    
    # Verify call_next was called once
    mock_call_next.assert_called_once_with(mock_request)
    
    # Verify the original response is returned
    assert response == mock_response


@test("middleware: forbidden, if user is not found")
async def _():
    """Test that requests resulting in NoDataFoundError from get_user_cost return 403."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    
    # Mock the get_user_cost function to raise NoDataFoundError
    with patch("agents_api.web.get_user_cost", new=AsyncMock(side_effect=asyncpg.NoDataFoundError())):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.body.decode()
        assert "invalid_user_account" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()
    
    http_404_error = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    with patch("agents_api.web.get_user_cost", new=AsyncMock(side_effect=http_404_error)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify response is 403 with correct message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid user account" in response.body.decode()
        assert "invalid_user_account" in response.body.decode()
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: non-404 HTTPException returns correct status")
async def _():
    """Test that HTTP exceptions other than 404 from get_user_cost return with correct status code."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    
    # Mock the get_user_cost function to raise HTTPException with 500
    http_500_error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    
    with patch("agents_api.web.get_user_cost", new=AsyncMock(side_effect=http_500_error)):
        # Set up mock for call_next
        mock_call_next = AsyncMock()
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify the response has the same status code as the exception
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Verify call_next was not called
        mock_call_next.assert_not_called()


@test("middleware: invalid uuid returns 400")
async def _():
    """Test that requests with invalid UUID return 400 Bad Request."""
    # Create mock request with invalid UUID
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": "invalid-uuid"})  # Invalid UUID
    
    # Set up mock for call_next
    mock_call_next = AsyncMock()
    
    # Call the middleware
    response = await usage_check_middleware(mock_request, mock_call_next)
    
    # Verify response is 400 with correct message
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid developer ID" in response.body.decode()
    assert "invalid_developer_id" in response.body.decode()
    
    # Verify call_next was not called
    mock_call_next.assert_not_called()


@test("middleware: other exceptions pass through")
async def _():
    """Test that other exceptions in the middleware don't block the request."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    
    # Create a mock response for call_next
    mock_response = JSONResponse(content={"message": "Success"})
    
    # Mock the get_user_cost function to raise a different exception
    with patch("agents_api.web.get_user_cost", new=AsyncMock(side_effect=KeyError("Unexpected error"))):
        # Set up mock for call_next
        mock_call_next = AsyncMock(return_value=mock_response)
        
        # We'll also mock logger.error to verify it's called
        with patch("agents_api.web.logger.error") as mock_logger_error:
            # Call the middleware
            response = await usage_check_middleware(mock_request, mock_call_next)
            
            # Verify logger.error was called
            mock_logger_error.assert_called_once()
            
            # Verify call_next was called once
            mock_call_next.assert_called_once_with(mock_request)
            
            # Verify the original response is returned
            assert response == mock_response


@test("middleware: valid user passes through")
async def _():
    """Test that requests from valid users are allowed to proceed."""
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = Headers({"X-Developer-Id": str(uuid.uuid4())})
    mock_request.method = "POST"
    
    # Mock response from get_user_cost
    mock_user_cost_data = {
        "active": True,
        "cost": 0.0,  # Below the limit
        "developer_id": mock_request.headers["X-Developer-Id"],
        "tags": []
    }
    
    # Create a mock response for call_next
    mock_response = JSONResponse(content={"message": "Success"})
    
    # Mock the get_user_cost function
    with patch("agents_api.web.get_user_cost", new=AsyncMock(return_value=mock_user_cost_data)):
        # Set up mock for call_next
        mock_call_next = AsyncMock(return_value=mock_response)
        
        # Call the middleware
        response = await usage_check_middleware(mock_request, mock_call_next)
        
        # Verify call_next was called once
        mock_call_next.assert_called_once_with(mock_request)
        
        # Verify the original response is returned
        assert response == mock_response 
