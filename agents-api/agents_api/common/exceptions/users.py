"""This module defines custom exceptions related to user operations in the agents-api."""

from uuid import UUID

from . import BaseCommonException


class BaseUserException(BaseCommonException):
    """
    Base exception class for user-related errors.

    This class serves as a parent for all user-related exceptions to facilitate catching errors specific to user operations.
    """


class UserNotFoundError(BaseUserException):
    """
    Exception raised when a requested user cannot be found.
    Attributes:
        developer_id (UUID | str): The ID of the developer attempting the operation.
        user_id (UUID | str): The ID of the user that was not found.
    """

    def __init__(self, developer_id: UUID | str, user_id: UUID | str):
        # Construct an error message indicating the user and developer involved in the error.
        super().__init__(
            f"User {user_id!s} not found for developer {developer_id!s}",
            http_code=404,
        )


class UserDocNotFoundError(BaseUserException):
    """
    Exception raised when a specific document related to a user cannot be found.
    Attributes:
        user_id (UUID | str): The ID of the user associated with the document.
        doc_id (UUID | str): The ID of the document that was not found.
    """

    def __init__(self, user_id: UUID | str, doc_id: UUID | str):
        # Construct an error message indicating the document and user involved in the error.
        super().__init__(f"Doc {doc_id!s} not found for user {user_id!s}", http_code=404)
