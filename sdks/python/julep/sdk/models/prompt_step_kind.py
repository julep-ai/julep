from enum import Enum


class PromptStepKind(str, Enum):
    PROMPT = "prompt"

    def __str__(self) -> str:
        return str(self.value)
