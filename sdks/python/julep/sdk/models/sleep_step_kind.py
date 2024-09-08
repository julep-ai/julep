from enum import Enum


class SleepStepKind(str, Enum):
    SLEEP = "sleep"

    def __str__(self) -> str:
        return str(self.value)
