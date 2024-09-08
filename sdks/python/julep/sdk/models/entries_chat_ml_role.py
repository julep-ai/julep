from enum import Enum


class EntriesChatMLRole(str, Enum):
    ASSISTANT = "assistant"
    AUTO = "auto"
    FUNCTION = "function"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESPONSE = "function_response"
    SYSTEM = "system"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
