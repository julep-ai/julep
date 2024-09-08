from enum import Enum


class JobState(str, Enum):
    ABORTED = "aborted"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)
