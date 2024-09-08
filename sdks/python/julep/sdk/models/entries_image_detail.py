from enum import Enum


class EntriesImageDetail(str, Enum):
    AUTO = "auto"
    HIGH = "high"
    LOW = "low"

    def __str__(self) -> str:
        return str(self.value)
