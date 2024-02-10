[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](index.md) / JulepApi

# Namespace: JulepApi

[index](index.md).JulepApi

## Table of contents

### Interfaces

- [Agent](../interfaces/index.JulepApi.Agent.md)
- [AgentDefaultSettings](../interfaces/index.JulepApi.AgentDefaultSettings.md)
- [Belief](../interfaces/index.JulepApi.Belief.md)
- [ChatInput](../interfaces/index.JulepApi.ChatInput.md)
- [ChatInputData](../interfaces/index.JulepApi.ChatInputData.md)
- [ChatMlMessage](../interfaces/index.JulepApi.ChatMlMessage.md)
- [ChatResponse](../interfaces/index.JulepApi.ChatResponse.md)
- [ChatSettings](../interfaces/index.JulepApi.ChatSettings.md)
- [ChatSettingsResponseFormat](../interfaces/index.JulepApi.ChatSettingsResponseFormat.md)
- [CompletionUsage](../interfaces/index.JulepApi.CompletionUsage.md)
- [CreateAgentRequest](../interfaces/index.JulepApi.CreateAgentRequest.md)
- [CreateDoc](../interfaces/index.JulepApi.CreateDoc.md)
- [CreateSessionRequest](../interfaces/index.JulepApi.CreateSessionRequest.md)
- [CreateToolRequest](../interfaces/index.JulepApi.CreateToolRequest.md)
- [CreateUserRequest](../interfaces/index.JulepApi.CreateUserRequest.md)
- [Doc](../interfaces/index.JulepApi.Doc.md)
- [Entity](../interfaces/index.JulepApi.Entity.md)
- [Episode](../interfaces/index.JulepApi.Episode.md)
- [FunctionCallOption](../interfaces/index.JulepApi.FunctionCallOption.md)
- [FunctionDef](../interfaces/index.JulepApi.FunctionDef.md)
- [GetAgentDocsRequest](../interfaces/index.JulepApi.GetAgentDocsRequest.md)
- [GetAgentDocsResponse](../interfaces/index.JulepApi.GetAgentDocsResponse.md)
- [GetAgentMemoriesRequest](../interfaces/index.JulepApi.GetAgentMemoriesRequest.md)
- [GetAgentMemoriesResponse](../interfaces/index.JulepApi.GetAgentMemoriesResponse.md)
- [GetAgentToolsRequest](../interfaces/index.JulepApi.GetAgentToolsRequest.md)
- [GetAgentToolsResponse](../interfaces/index.JulepApi.GetAgentToolsResponse.md)
- [GetHistoryRequest](../interfaces/index.JulepApi.GetHistoryRequest.md)
- [GetHistoryResponse](../interfaces/index.JulepApi.GetHistoryResponse.md)
- [GetSuggestionsRequest](../interfaces/index.JulepApi.GetSuggestionsRequest.md)
- [GetSuggestionsResponse](../interfaces/index.JulepApi.GetSuggestionsResponse.md)
- [GetUserDocsRequest](../interfaces/index.JulepApi.GetUserDocsRequest.md)
- [GetUserDocsResponse](../interfaces/index.JulepApi.GetUserDocsResponse.md)
- [InputChatMlMessage](../interfaces/index.JulepApi.InputChatMlMessage.md)
- [Instruction](../interfaces/index.JulepApi.Instruction.md)
- [ListAgentsRequest](../interfaces/index.JulepApi.ListAgentsRequest.md)
- [ListAgentsResponse](../interfaces/index.JulepApi.ListAgentsResponse.md)
- [ListSessionsRequest](../interfaces/index.JulepApi.ListSessionsRequest.md)
- [ListSessionsResponse](../interfaces/index.JulepApi.ListSessionsResponse.md)
- [ListUsersRequest](../interfaces/index.JulepApi.ListUsersRequest.md)
- [ListUsersResponse](../interfaces/index.JulepApi.ListUsersResponse.md)
- [MemoryAccessOptions](../interfaces/index.JulepApi.MemoryAccessOptions.md)
- [NamedToolChoice](../interfaces/index.JulepApi.NamedToolChoice.md)
- [NamedToolChoiceFunction](../interfaces/index.JulepApi.NamedToolChoiceFunction.md)
- [ResourceCreatedResponse](../interfaces/index.JulepApi.ResourceCreatedResponse.md)
- [ResourceDeletedResponse](../interfaces/index.JulepApi.ResourceDeletedResponse.md)
- [ResourceUpdatedResponse](../interfaces/index.JulepApi.ResourceUpdatedResponse.md)
- [Session](../interfaces/index.JulepApi.Session.md)
- [Suggestion](../interfaces/index.JulepApi.Suggestion.md)
- [Tool](../interfaces/index.JulepApi.Tool.md)
- [UpdateAgentRequest](../interfaces/index.JulepApi.UpdateAgentRequest.md)
- [UpdateSessionRequest](../interfaces/index.JulepApi.UpdateSessionRequest.md)
- [UpdateToolRequest](../interfaces/index.JulepApi.UpdateToolRequest.md)
- [UpdateUserRequest](../interfaces/index.JulepApi.UpdateUserRequest.md)
- [User](../interfaces/index.JulepApi.User.md)

### Type Aliases

- [ChatMlMessageRole](index.JulepApi.md#chatmlmessagerole)
- [ChatResponseFinishReason](index.JulepApi.md#chatresponsefinishreason)
- [ChatSettingsResponseFormatType](index.JulepApi.md#chatsettingsresponseformattype)
- [ChatSettingsStop](index.JulepApi.md#chatsettingsstop)
- [CreateToolRequestType](index.JulepApi.md#createtoolrequesttype)
- [FunctionParameters](index.JulepApi.md#functionparameters)
- [InputChatMlMessageRole](index.JulepApi.md#inputchatmlmessagerole)
- [Memory](index.JulepApi.md#memory)
- [SuggestionTarget](index.JulepApi.md#suggestiontarget)
- [ToolChoiceOption](index.JulepApi.md#toolchoiceoption)
- [ToolType](index.JulepApi.md#tooltype)

### Variables

- [ChatMlMessageRole](index.JulepApi.md#chatmlmessagerole-1)
- [ChatResponseFinishReason](index.JulepApi.md#chatresponsefinishreason-1)
- [ChatSettingsResponseFormatType](index.JulepApi.md#chatsettingsresponseformattype-1)
- [CreateToolRequestType](index.JulepApi.md#createtoolrequesttype-1)
- [InputChatMlMessageRole](index.JulepApi.md#inputchatmlmessagerole-1)
- [SuggestionTarget](index.JulepApi.md#suggestiontarget-1)
- [ToolType](index.JulepApi.md#tooltype-1)

## Type Aliases

### ChatMlMessageRole

Ƭ **ChatMlMessageRole**: ``"user"`` \| ``"assistant"`` \| ``"system"`` \| ``"function_call"``

ChatML role (system|assistant|user|function_call)

#### Defined in

[src/api/api/types/ChatMlMessageRole.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatMlMessageRole.d.ts#L7)

[src/api/api/types/ChatMlMessageRole.d.ts:12](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatMlMessageRole.d.ts#L12)

___

### ChatResponseFinishReason

Ƭ **ChatResponseFinishReason**: ``"stop"`` \| ``"length"`` \| ``"tool_calls"`` \| ``"content_filter"`` \| ``"function_call"``

The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function.

#### Defined in

[src/api/api/types/ChatResponseFinishReason.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L7)

[src/api/api/types/ChatResponseFinishReason.d.ts:13](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L13)

___

### ChatSettingsResponseFormatType

Ƭ **ChatSettingsResponseFormatType**: ``"text"`` \| ``"json_object"``

Must be one of `text` or `json_object`.

#### Defined in

[src/api/api/types/ChatSettingsResponseFormatType.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatSettingsResponseFormatType.d.ts#L7)

[src/api/api/types/ChatSettingsResponseFormatType.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatSettingsResponseFormatType.d.ts#L8)

___

### ChatSettingsStop

Ƭ **ChatSettingsStop**: `string` \| `undefined` \| `string`[]

Up to 4 sequences where the API will stop generating further tokens.

#### Defined in

[src/api/api/types/ChatSettingsStop.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatSettingsStop.d.ts#L7)

___

### CreateToolRequestType

Ƭ **CreateToolRequestType**: ``"function"`` \| ``"webhook"``

Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now)

#### Defined in

[src/api/api/types/CreateToolRequestType.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/CreateToolRequestType.d.ts#L7)

[src/api/api/types/CreateToolRequestType.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/CreateToolRequestType.d.ts#L8)

___

### FunctionParameters

Ƭ **FunctionParameters**: `Record`\<`string`, `unknown`\>

The parameters the functions accepts, described as a JSON Schema object.

#### Defined in

[src/api/api/types/FunctionParameters.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/FunctionParameters.d.ts#L7)

___

### InputChatMlMessageRole

Ƭ **InputChatMlMessageRole**: ``"user"`` \| ``"assistant"`` \| ``"system"`` \| ``"function_call"``

ChatML role (system|assistant|user|function_call)

#### Defined in

[src/api/api/types/InputChatMlMessageRole.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/InputChatMlMessageRole.d.ts#L7)

[src/api/api/types/InputChatMlMessageRole.d.ts:12](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/InputChatMlMessageRole.d.ts#L12)

___

### Memory

Ƭ **Memory**: [`Belief`](../interfaces/index.JulepApi.Belief.md) \| [`Episode`](../interfaces/index.JulepApi.Episode.md) \| [`Entity`](../interfaces/index.JulepApi.Entity.md)

#### Defined in

[src/api/api/types/Memory.d.ts:5](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Memory.d.ts#L5)

___

### SuggestionTarget

Ƭ **SuggestionTarget**: ``"user"`` \| ``"agent"``

Whether the suggestion is for the `agent` or a `user`

#### Defined in

[src/api/api/types/SuggestionTarget.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/SuggestionTarget.d.ts#L7)

[src/api/api/types/SuggestionTarget.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/SuggestionTarget.d.ts#L8)

___

### ToolChoiceOption

Ƭ **ToolChoiceOption**: `string`

Controls which (if any) function is called by the model.
`none` means the model will not call a function and instead generates a message.
`auto` means the model can pick between generating a message or calling a function.
Specifying a particular function via `{"type: "function", "function": {"name": "my_function"}}` forces the model to call that function.

`none` is the default when no functions are present. `auto` is the default if functions are present.

#### Defined in

[src/api/api/types/ToolChoiceOption.d.ts:12](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ToolChoiceOption.d.ts#L12)

___

### ToolType

Ƭ **ToolType**: ``"function"`` \| ``"webhook"``

Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now)

#### Defined in

[src/api/api/types/ToolType.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ToolType.d.ts#L7)

[src/api/api/types/ToolType.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ToolType.d.ts#L8)

## Variables

### ChatMlMessageRole

• **ChatMlMessageRole**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `Assistant` | ``"assistant"`` |
| `FunctionCall` | ``"function_call"`` |
| `System` | ``"system"`` |
| `User` | ``"user"`` |

#### Defined in

[src/api/api/types/ChatMlMessageRole.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatMlMessageRole.d.ts#L7)

[src/api/api/types/ChatMlMessageRole.d.ts:12](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatMlMessageRole.d.ts#L12)

___

### ChatResponseFinishReason

• **ChatResponseFinishReason**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `ContentFilter` | ``"content_filter"`` |
| `FunctionCall` | ``"function_call"`` |
| `Length` | ``"length"`` |
| `Stop` | ``"stop"`` |
| `ToolCalls` | ``"tool_calls"`` |

#### Defined in

[src/api/api/types/ChatResponseFinishReason.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L7)

[src/api/api/types/ChatResponseFinishReason.d.ts:13](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatResponseFinishReason.d.ts#L13)

___

### ChatSettingsResponseFormatType

• **ChatSettingsResponseFormatType**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `JsonObject` | ``"json_object"`` |
| `Text` | ``"text"`` |

#### Defined in

[src/api/api/types/ChatSettingsResponseFormatType.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatSettingsResponseFormatType.d.ts#L7)

[src/api/api/types/ChatSettingsResponseFormatType.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ChatSettingsResponseFormatType.d.ts#L8)

___

### CreateToolRequestType

• **CreateToolRequestType**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `Function` | ``"function"`` |
| `Webhook` | ``"webhook"`` |

#### Defined in

[src/api/api/types/CreateToolRequestType.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/CreateToolRequestType.d.ts#L7)

[src/api/api/types/CreateToolRequestType.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/CreateToolRequestType.d.ts#L8)

___

### InputChatMlMessageRole

• **InputChatMlMessageRole**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `Assistant` | ``"assistant"`` |
| `FunctionCall` | ``"function_call"`` |
| `System` | ``"system"`` |
| `User` | ``"user"`` |

#### Defined in

[src/api/api/types/InputChatMlMessageRole.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/InputChatMlMessageRole.d.ts#L7)

[src/api/api/types/InputChatMlMessageRole.d.ts:12](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/InputChatMlMessageRole.d.ts#L12)

___

### SuggestionTarget

• **SuggestionTarget**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `Agent` | ``"agent"`` |
| `User` | ``"user"`` |

#### Defined in

[src/api/api/types/SuggestionTarget.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/SuggestionTarget.d.ts#L7)

[src/api/api/types/SuggestionTarget.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/SuggestionTarget.d.ts#L8)

___

### ToolType

• **ToolType**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `Function` | ``"function"`` |
| `Webhook` | ``"webhook"`` |

#### Defined in

[src/api/api/types/ToolType.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ToolType.d.ts#L7)

[src/api/api/types/ToolType.d.ts:8](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/ToolType.d.ts#L8)
