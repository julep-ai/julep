from enum import Enum


class IfElseWorkflowStepKind(str, Enum):
    IF_ELSE = "if_else"

    def __str__(self) -> str:
        return str(self.value)
