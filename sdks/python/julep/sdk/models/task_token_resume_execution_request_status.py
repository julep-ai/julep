from enum import Enum


class TaskTokenResumeExecutionRequestStatus(str, Enum):
    RUNNING = "running"

    def __str__(self) -> str:
        return str(self.value)
