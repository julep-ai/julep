from enum import Enum


class ExecutionStatus(str, Enum):
    AWAITING_INPUT = "awaiting_input"
    CANCELLED = "cancelled"
    FAILED = "failed"
    QUEUED = "queued"
    RUNNING = "running"
    STARTING = "starting"
    SUCCEEDED = "succeeded"

    def __str__(self) -> str:
        return str(self.value)
