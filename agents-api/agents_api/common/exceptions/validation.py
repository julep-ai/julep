from . import BaseCommonException


class QueryParamsValidationError(BaseCommonException):
    """Exception raised for validation errors in query parameters."""

    def __init__(self, message: str) -> None:
        super().__init__(message, http_code=400)
