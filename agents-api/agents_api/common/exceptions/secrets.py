"""Custom exceptions for secrets management."""

from uuid import UUID

from . import BaseCommonException


class SecretNotFoundError(BaseCommonException):
    """Exception raised when a requested secret cannot be found."""

    def __init__(self, developer_id: UUID | str, name: str):
        super().__init__(
            f"Secret {name!s} not found for developer {developer_id!s}", http_code=404
        )
