from enum import Enum


class BaseEntrySource(str, Enum):
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    INTERNAL = "internal"
    META = "meta"
    SUMMARIZER = "summarizer"
    TOOL_RESPONSE = "tool_response"

    def __str__(self) -> str:
        return str(self.value)
