"""
This module defines a structured hierarchy of custom exceptions for the agents API, aimed at handling specific error scenarios encountered across various operations. These exceptions are designed to provide clear, actionable error messages and appropriate HTTP status codes, enhancing the API's robustness and usability.

Exceptions are organized into categories based on the domain of operation, including:
- Agent-related operations (agents.py): Exceptions such as `AgentNotFoundError` and `AgentToolNotFoundError` cater to errors specific to agent management.
- Session management (sessions.py): Defines exceptions like `SessionNotFoundError` for handling errors related to session operations.
- User interactions (users.py): Includes exceptions such as `UserNotFoundError` for addressing issues encountered during user-related operations.

All custom exceptions extend from `BaseCommonException`, which encapsulates common attributes and behavior, including the error message and HTTP status code. This structured approach to exception handling facilitates precise and meaningful error feedback to API consumers, thereby improving the overall developer experience.
"""


class BaseCommonException(Exception):
    def __init__(self, msg: str, http_code: int) -> None:
        super().__init__(msg)
        self.http_code = http_code
