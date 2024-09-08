from enum import Enum


class SwitchStepKind(str, Enum):
    SWITCH = "switch"

    def __str__(self) -> str:
        return str(self.value)
