# AIDEV-NOTE: This module defines custom exceptions specifically for tool-related operations.
"""
Defines tools-related exceptions for the agents API.
"""

from ...autogen.openapi_model import BaseIntegrationDef
from . import BaseCommonException


# AIDEV-NOTE: Base exception class for all tool-related errors, inheriting from BaseCommonException.
class BaseToolsException(BaseCommonException):
    """Base exception for tools-related errors."""


# AIDEV-NOTE: Exception raised when an error occurs during the execution of an integration tool.
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
