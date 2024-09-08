from enum import Enum


class FinishReason(str, Enum):
    CONTENT_FILTER = "content_filter"
    LENGTH = "length"
    STOP = "stop"
    TOOL_CALLS = "tool_calls"

    def __str__(self) -> str:
        return str(self.value)
