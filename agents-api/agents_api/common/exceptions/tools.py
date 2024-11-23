"""
Defines tools-related exceptions for the agents API.
"""

from ...autogen.openapi_model import BaseIntegrationDef
from . import BaseCommonException


class BaseToolsException(BaseCommonException):
    """Base exception for tools-related errors."""

    pass


class IntegrationExecutionException(BaseToolsException):
    """Exception raised when an error occurs during an integration execution."""

    def __init__(self, integration: BaseIntegrationDef, error: str):
        integration_str = integration.provider + (
            "." + integration.method if integration.method else ""
        )
        super().__init__(
            f"Error in executing {integration_str}: {error}",
            http_code=500,
        )
