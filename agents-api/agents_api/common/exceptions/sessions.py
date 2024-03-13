from uuid import UUID


class BaseSessionException(Exception):
    pass


class SessionNotFoundError(BaseSessionException):
    def __init__(self, developer_id: UUID | str, session_id: UUID | str):
        super().__init__(
            f"Session {str(session_id)} not found for developer {str(developer_id)}"
        )
