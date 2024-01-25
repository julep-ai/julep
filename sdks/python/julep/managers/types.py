from typing import TypedDict
from ..api.types import (
    CreateAdditionalInfoRequest,
    AgentDefaultSettings,
    FunctionDef,
    CreateToolRequest,
    Instruction,
)


DocDict = TypedDict(
    "DocDict",
    **{k: v.outer_type_ for k, v in CreateAdditionalInfoRequest.__fields__.items()},
)
DefaultSettingsDict = TypedDict(
    "DefaultSettingsDict",
    **{k: v.outer_type_ for k, v in AgentDefaultSettings.__fields__.items()},
)
FunctionDefDict = TypedDict(
    "FunctionDefDict", **{k: v.outer_type_ for k, v in FunctionDef.__fields__.items()}
)
ToolDict = TypedDict(
    "ToolDict", **{k: v.outer_type_ for k, v in CreateToolRequest.__fields__.items()}
)
InstructionDict = TypedDict(
    "InstructionDict", **{k: v.outer_type_ for k, v in Instruction.__fields__.items()}
)
