"""Common exception classes for Julep services."""


class JulepError(Exception):
    """Base exception for Julep."""


class TooManyRequestsError(JulepError):
    """Raised when a request rate limit is exceeded."""
