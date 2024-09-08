from enum import Enum


class LogStepKind(str, Enum):
    LOG = "log"

    def __str__(self) -> str:
        return str(self.value)
