from enum import Enum


class EmbedStepKind(str, Enum):
    EMBED = "embed"

    def __str__(self) -> str:
        return str(self.value)
