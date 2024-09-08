from enum import Enum


class SimpleCompletionResponseFormatType(str, Enum):
    JSON_OBJECT = "json_object"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)
