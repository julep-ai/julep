from enum import Enum


class TransitionEventType(str, Enum):
    CANCELLED = "cancelled"
    ERROR = "error"
    FINISH = "finish"
    FINISH_BRANCH = "finish_branch"
    INIT = "init"
    INIT_BRANCH = "init_branch"
    RESUME = "resume"
    STEP = "step"
    WAIT = "wait"

    def __str__(self) -> str:
        return str(self.value)
