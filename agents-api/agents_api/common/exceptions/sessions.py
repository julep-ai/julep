"""
Defines session-related exceptions for the agents API.

These exceptions are used throughout the agents API to handle errors related to session operations, such as when a requested session cannot be found.
"""

from uuid import UUID

from . import BaseCommonException


class BaseSessionException(BaseCommonException):
    """
    Base exception class for session-related errors.

    This class serves as a base for all session-related exceptions, allowing for a structured exception handling approach specific to session operations.
    """


class SessionNotFoundError(BaseSessionException):
    """
    Exception raised when a session cannot be found.

    This exception is used to indicate that a specific session, identified by its session ID, does not exist or is not accessible for the given developer.

    Attributes:
        developer_id (UUID | str): The unique identifier of the developer attempting to access the session.
        session_id (UUID | str): The unique identifier of the session that was not found.
    """

    def __init__(self, developer_id: UUID | str, session_id: UUID | str) -> None:
        super().__init__(
            f"Session {session_id!s} not found for developer {developer_id!s}",
            http_code=404,
        )
