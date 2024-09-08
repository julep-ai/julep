from enum import Enum


class WaitForInputStepKind(str, Enum):
    WAIT_FOR_INPUT = "wait_for_input"

    def __str__(self) -> str:
        return str(self.value)
