# type: ignore
# ^^ Added to ignore pytype errors for this file as it uses hacks
from typing import TypedDict
from ..api.types import (
    CreateDoc,
    AgentDefaultSettings,
    FunctionDef,
    CreateToolRequest,
    ChatSettingsResponseFormat,
    InputChatMlMessage,
    Tool,
)

# Represents the settings for chat response formatting, used in configuring agent chat behavior.
ChatSettingsResponseFormatDict = TypedDict(
    "ChatSettingsResponseFormat",
    **{k: v.outer_type_ for k, v in ChatSettingsResponseFormat.__fields__.items()},
)
# Represents an input message for chat in ML format, used for processing chat inputs.
InputChatMlMessageDict = TypedDict(
    "InputChatMlMessage",
    **{k: v.outer_type_ for k, v in InputChatMlMessage.__fields__.items()},
)
# Represents the structure of a tool, used for defining tools within the system.
ToolDict = TypedDict(
    "Tool",
    **{k: v.outer_type_ for k, v in Tool.__fields__.items()},
)

# Represents the serialized form of a document, used for API communication.
DocDict = TypedDict(
    "DocDict",
    **{k: v.outer_type_ for k, v in CreateDoc.__fields__.items()},
)
# Represents the default settings for an agent, used in agent configuration.
DefaultSettingsDict = TypedDict(
    "DefaultSettingsDict",
    **{k: v.outer_type_ for k, v in AgentDefaultSettings.__fields__.items()},
)
# Represents the definition of a function, used for defining functions within the system.
FunctionDefDict = TypedDict(
    "FunctionDefDict", **{k: v.outer_type_ for k, v in FunctionDef.__fields__.items()}
)
# Represents the request structure for creating a tool, used in tool creation API calls.
ToolDict = TypedDict(
    "ToolDict", **{k: v.outer_type_ for k, v in CreateToolRequest.__fields__.items()}
)
