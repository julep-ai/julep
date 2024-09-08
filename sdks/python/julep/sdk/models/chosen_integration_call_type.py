from enum import Enum


class ChosenIntegrationCallType(str, Enum):
    INTEGRATION = "integration"

    def __str__(self) -> str:
        return str(self.value)
