from enum import Enum


class ToolType(str, Enum):
    API_CALL = "api_call"
    FUNCTION = "function"
    INTEGRATION = "integration"
    SYSTEM = "system"

    def __str__(self) -> str:
        return str(self.value)
