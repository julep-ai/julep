from enum import Enum


class ForeachStepKind(str, Enum):
    FOREACH = "foreach"

    def __str__(self) -> str:
        return str(self.value)
