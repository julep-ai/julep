# type: ignore
# ^^ Added to ignore pytype errors for this file as it uses hacks
from typing import TypedDict
from ..api.types import (
    CreateDoc,
    AgentDefaultSettings,
    FunctionDef,
    CreateToolRequest,
    Instruction,
    ChatSettingsResponseFormat,
    InputChatMlMessage,
    Tool,
)

ChatSettingsResponseFormatDict = TypedDict(
    "ChatSettingsResponseFormat",
    **{k: v.outer_type_ for k, v in ChatSettingsResponseFormat.__fields__.items()},
)
InputChatMlMessageDict = TypedDict(
    "InputChatMlMessage",
    **{k: v.outer_type_ for k, v in InputChatMlMessage.__fields__.items()},
)
ToolDict = TypedDict(
    "Tool",
    **{k: v.outer_type_ for k, v in Tool.__fields__.items()},
)

DocDict = TypedDict(
    "DocDict",
    **{k: v.outer_type_ for k, v in CreateDoc.__fields__.items()},
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
