from enum import Enum


class ChatInputToolChoiceType0(str, Enum):
    AUTO = "auto"
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
