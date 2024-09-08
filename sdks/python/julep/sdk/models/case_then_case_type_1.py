from enum import Enum


class CaseThenCaseType1(str, Enum):
    VALUE_0 = "_"

    def __str__(self) -> str:
        return str(self.value)
