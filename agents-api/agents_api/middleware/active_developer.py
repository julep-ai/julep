"""
Middleware for checking if a developer is active based on X-Developer-Id header.

This middleware applies to all routes and verifies that the developer
has active status in the database before proceeding with the request.
"""

from uuid import UUID

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_403_FORBIDDEN

from ..env import multi_tenant_mode
from ..queries.developers.get_developer import get_developer


class ActiveDeveloperMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks if the developer from X-Developer-Id header is active.

    This middleware extracts the developer_id from the X-Developer-Id header
    and verifies that the developer has active status in the database
    before allowing the request to proceed.
    """

    async def _get_developer(self, developer_id: UUID):
        try:
            # The get_developer function already filters on active=true
            await get_developer(developer_id=developer_id)
            # If no exception, developer is active
        except Exception:
            # Developer not found or not active
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Developer account is not active",
            )

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and check if the developer is active.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            The response from the next middleware or endpoint
        """
        # Skip authentication for some paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        # Skip in single-tenant mode
        if not multi_tenant_mode:
            return await call_next(request)

        # Get the X-Developer-Id header
        developer_id_header = request.headers.get("X-Developer-Id")
        if not developer_id_header:
            return await call_next(request)  # Let it fail at the route level if required

        try:
            # Convert to UUID
            developer_id = UUID(developer_id_header)
            await self._get_developer(developer_id)
            # Continue processing the request
            return await call_next(request)
        except ValueError:
            # Invalid UUID format - let it fail at the route level if auth is required
            return await call_next(request)

    @staticmethod
    def _should_skip_auth(path: str) -> bool:
        """
        Determine if authentication should be skipped for a path.

        Args:
            path: The request path

        Returns:
            True if authentication should be skipped, False otherwise
        """
        # Skip auth for health checks, docs, etc.
        skip_prefixes = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/healthz",
        ]

        return any(path.startswith(prefix) for prefix in skip_prefixes)
