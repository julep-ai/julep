from uuid import UUID
from . import BaseCommonException


class BaseUserException(BaseCommonException):
    pass


class UserNotFoundError(BaseUserException):
    def __init__(self, developer_id: UUID | str, user_id: UUID | str):
        super().__init__(
            f"User {str(user_id)} not found for developer {str(developer_id)}",
            http_code=404,
        )


class UserDocNotFoundError(BaseUserException):
    def __init__(self, user_id: UUID | str, doc_id: UUID | str):
        super().__init__(
            f"Doc {str(doc_id)} not found for user {str(user_id)}", http_code=404
        )
