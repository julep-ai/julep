from enum import Enum


class BaseEntryContentType0ItemType0Type(str, Enum):
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)
