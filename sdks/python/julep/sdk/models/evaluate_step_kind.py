from enum import Enum


class EvaluateStepKind(str, Enum):
    EVALUATE = "evaluate"

    def __str__(self) -> str:
        return str(self.value)
