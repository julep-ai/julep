from enum import Enum


class ContextOverflowType(str, Enum):
    ADAPTIVE = "adaptive"
    TRUNCATE = "truncate"

    def __str__(self) -> str:
        return str(self.value)
