from enum import Enum


class SearchStepKind(str, Enum):
    SEARCH = "search"

    def __str__(self) -> str:
        return str(self.value)
