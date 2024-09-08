from enum import Enum


class ParallelStepKind(str, Enum):
    PARALLEL = "parallel"

    def __str__(self) -> str:
        return str(self.value)
