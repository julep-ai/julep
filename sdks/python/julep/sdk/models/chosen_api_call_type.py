from enum import Enum


class ChosenApiCallType(str, Enum):
    API_CALL = "api_call"

    def __str__(self) -> str:
        return str(self.value)
