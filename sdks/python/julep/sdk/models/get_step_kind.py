from enum import Enum


class GetStepKind(str, Enum):
    GET = "get"

    def __str__(self) -> str:
        return str(self.value)
