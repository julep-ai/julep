from enum import Enum


class YieldStepKind(str, Enum):
    YIELD = "yield"

    def __str__(self) -> str:
        return str(self.value)
