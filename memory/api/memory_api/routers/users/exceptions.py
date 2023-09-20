class BaseUserException(Exception):
    pass


class InvalidUserQueryError(BaseUserException):
    def __init__(self, message: str):
        super().__init__(f"Invalid user query: {message}")
