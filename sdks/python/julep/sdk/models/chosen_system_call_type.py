from enum import Enum


class ChosenSystemCallType(str, Enum):
    SYSTEM = "system"

    def __str__(self) -> str:
        return str(self.value)
