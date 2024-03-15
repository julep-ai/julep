from uuid import UUID
from . import BaseCommonException


class BaseSessionException(BaseCommonException):
    pass


class SessionNotFoundError(BaseSessionException):
    def __init__(self, developer_id: UUID | str, session_id: UUID | str):
        super().__init__(
            f"Session {str(session_id)} not found for developer {str(developer_id)}",
            http_code=404,
        )
