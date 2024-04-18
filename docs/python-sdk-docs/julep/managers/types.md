# Types

[Julep Python SDK Index](../../README.md#julep-python-sdk-index) / [Julep](../index.md#julep) / [Managers](./index.md#managers) / Types

> Auto-generated documentation for [julep.managers.types](../../../../../../julep/managers/types.py) module.

#### Attributes

- `ChatSettingsResponseFormatDict` - Represents the settings for chat response formatting, used in configuring agent chat behavior.: TypedDict('ChatSettingsResponseFormat', **{k: v.outer_type_ for (k, v) in ChatSettingsResponseFormat.__fields__.items()})

- `InputChatMlMessageDict` - Represents an input message for chat in ML format, used for processing chat inputs.: TypedDict('InputChatMlMessage', **{k: v.outer_type_ for (k, v) in InputChatMlMessage.__fields__.items()})

- `ToolDict` - Represents the structure of a tool, used for defining tools within the system.: TypedDict('Tool', **{k: v.outer_type_ for (k, v) in Tool.__fields__.items()})

- `DocDict` - Represents the serialized form of a document, used for API communication.: TypedDict('DocDict', **{k: v.outer_type_ for (k, v) in CreateDoc.__fields__.items()})

- `DefaultSettingsDict` - Represents the default settings for an agent, used in agent configuration.: TypedDict('DefaultSettingsDict', **{k: v.outer_type_ for (k, v) in AgentDefaultSettings.__fields__.items()})

- `FunctionDefDict` - Represents the definition of a function, used for defining functions within the system.: TypedDict('FunctionDefDict', **{k: v.outer_type_ for (k, v) in FunctionDef.__fields__.items()})

- `ToolDict` - Represents the request structure for creating a tool, used in tool creation API calls.: TypedDict('ToolDict', **{k: v.outer_type_ for (k, v) in CreateToolRequest.__fields__.items()})
- [Types](#types)
