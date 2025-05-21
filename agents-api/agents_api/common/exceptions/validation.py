# AIDEV-NOTE: This module defines custom exceptions specifically for validation errors.
from . import BaseCommonException


# AIDEV-NOTE: Exception raised for validation errors in query parameters.
class QueryParamsValidationError(BaseCommonException):
    """Exception raised for validation errors in query parameters."""

    def __init__(self, message: str) -> None:
        super().__init__(message, http_code=400)
