from enum import Enum


class ReturnStepKind(str, Enum):
    RETURN = "return"

    def __str__(self) -> str:
        return str(self.value)
