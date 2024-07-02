[@julep/sdk](../README.md) / [Modules](../modules.md) / api

# Module: api

## Table of contents

### References

- [JulepApiClient](api.md#julepapiclient)

### Classes

- [ApiError](../classes/api.ApiError.md)
- [BaseHttpRequest](../classes/api.BaseHttpRequest.md)
- [CancelError](../classes/api.CancelError.md)
- [CancelablePromise](../classes/api.CancelablePromise.md)
- [DefaultService](../classes/api.DefaultService.md)

### Type Aliases

- [Agent](api.md#agent)
- [AgentDefaultSettings](api.md#agentdefaultsettings)
- [ChatInput](api.md#chatinput)
- [ChatInputData](api.md#chatinputdata)
- [ChatMLImageContentPart](api.md#chatmlimagecontentpart)
- [ChatMLMessage](api.md#chatmlmessage)
- [ChatMLTextContentPart](api.md#chatmltextcontentpart)
- [ChatResponse](api.md#chatresponse)
- [ChatSettings](api.md#chatsettings)
- [CompletionUsage](api.md#completionusage)
- [CreateAgentRequest](api.md#createagentrequest)
- [CreateDoc](api.md#createdoc)
- [CreateSessionRequest](api.md#createsessionrequest)
- [CreateToolRequest](api.md#createtoolrequest)
- [CreateUserRequest](api.md#createuserrequest)
- [Doc](api.md#doc)
- [DocIds](api.md#docids)
- [FunctionCallOption](api.md#functioncalloption)
- [FunctionDef](api.md#functiondef)
- [FunctionParameters](api.md#functionparameters)
- [InputChatMLMessage](api.md#inputchatmlmessage)
- [JobStatus](api.md#jobstatus)
- [Memory](api.md#memory)
- [MemoryAccessOptions](api.md#memoryaccessoptions)
- [NamedToolChoice](api.md#namedtoolchoice)
- [OpenAPIConfig](api.md#openapiconfig)
- [PartialFunctionDef](api.md#partialfunctiondef)
- [PatchAgentRequest](api.md#patchagentrequest)
- [PatchSessionRequest](api.md#patchsessionrequest)
- [PatchToolRequest](api.md#patchtoolrequest)
- [PatchUserRequest](api.md#patchuserrequest)
- [ResourceCreatedResponse](api.md#resourcecreatedresponse)
- [ResourceDeletedResponse](api.md#resourcedeletedresponse)
- [ResourceUpdatedResponse](api.md#resourceupdatedresponse)
- [Session](api.md#session)
- [Suggestion](api.md#suggestion)
- [Tool](api.md#tool)
- [ToolChoiceOption](api.md#toolchoiceoption)
- [UpdateAgentRequest](api.md#updateagentrequest)
- [UpdateSessionRequest](api.md#updatesessionrequest)
- [UpdateToolRequest](api.md#updatetoolrequest)
- [UpdateUserRequest](api.md#updateuserrequest)
- [User](api.md#user)
- [agent\_id](api.md#agent_id)
- [doc\_id](api.md#doc_id)
- [job\_id](api.md#job_id)
- [memory\_id](api.md#memory_id)
- [message\_id](api.md#message_id)
- [session\_id](api.md#session_id)
- [tool\_id](api.md#tool_id)
- [user\_id](api.md#user_id)

### Variables

- [$Agent](api.md#$agent)
- [$AgentDefaultSettings](api.md#$agentdefaultsettings)
- [$ChatInput](api.md#$chatinput)
- [$ChatInputData](api.md#$chatinputdata)
- [$ChatMLImageContentPart](api.md#$chatmlimagecontentpart)
- [$ChatMLMessage](api.md#$chatmlmessage)
- [$ChatMLTextContentPart](api.md#$chatmltextcontentpart)
- [$ChatResponse](api.md#$chatresponse)
- [$ChatSettings](api.md#$chatsettings)
- [$CompletionUsage](api.md#$completionusage)
- [$CreateAgentRequest](api.md#$createagentrequest)
- [$CreateDoc](api.md#$createdoc)
- [$CreateSessionRequest](api.md#$createsessionrequest)
- [$CreateToolRequest](api.md#$createtoolrequest)
- [$CreateUserRequest](api.md#$createuserrequest)
- [$Doc](api.md#$doc)
- [$DocIds](api.md#$docids)
- [$FunctionCallOption](api.md#$functioncalloption)
- [$FunctionDef](api.md#$functiondef)
- [$FunctionParameters](api.md#$functionparameters)
- [$InputChatMLMessage](api.md#$inputchatmlmessage)
- [$JobStatus](api.md#$jobstatus)
- [$Memory](api.md#$memory)
- [$MemoryAccessOptions](api.md#$memoryaccessoptions)
- [$NamedToolChoice](api.md#$namedtoolchoice)
- [$PartialFunctionDef](api.md#$partialfunctiondef)
- [$PatchAgentRequest](api.md#$patchagentrequest)
- [$PatchSessionRequest](api.md#$patchsessionrequest)
- [$PatchToolRequest](api.md#$patchtoolrequest)
- [$PatchUserRequest](api.md#$patchuserrequest)
- [$ResourceCreatedResponse](api.md#$resourcecreatedresponse)
- [$ResourceDeletedResponse](api.md#$resourcedeletedresponse)
- [$ResourceUpdatedResponse](api.md#$resourceupdatedresponse)
- [$Session](api.md#$session)
- [$Suggestion](api.md#$suggestion)
- [$Tool](api.md#$tool)
- [$ToolChoiceOption](api.md#$toolchoiceoption)
- [$UpdateAgentRequest](api.md#$updateagentrequest)
- [$UpdateSessionRequest](api.md#$updatesessionrequest)
- [$UpdateToolRequest](api.md#$updatetoolrequest)
- [$UpdateUserRequest](api.md#$updateuserrequest)
- [$User](api.md#$user)
- [$agent\_id](api.md#$agent_id)
- [$doc\_id](api.md#$doc_id)
- [$job\_id](api.md#$job_id)
- [$memory\_id](api.md#$memory_id)
- [$message\_id](api.md#$message_id)
- [$session\_id](api.md#$session_id)
- [$tool\_id](api.md#$tool_id)
- [$user\_id](api.md#$user_id)
- [OpenAPI](api.md#openapi)

## References

### JulepApiClient

Re-exports [JulepApiClient](../classes/api_JulepApiClient.JulepApiClient.md)

## Type Aliases

### Agent

Ƭ **Agent**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the agent |
| `created_at?` | `string` | Agent created at (RFC-3339 format) |
| `default_settings?` | [`AgentDefaultSettings`](api.md#agentdefaultsettings) | Default settings for all sessions created by this agent |
| `id` | `string` | Agent id (UUID) |
| `instructions?` | `string` \| `string`[] | Instructions for the agent |
| `metadata?` | `any` | Optional metadata |
| `model` | `string` | The model to use with this agent |
| `name` | `string` | Name of the agent |
| `updated_at?` | `string` | Agent updated at (RFC-3339 format) |

#### Defined in

[src/api/models/Agent.ts:6](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/Agent.ts#L6)

___

### AgentDefaultSettings

Ƭ **AgentDefaultSettings**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `frequency_penalty?` | `number` \| ``null`` | (OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `length_penalty?` | `number` \| ``null`` | (Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. |
| `min_p?` | `number` | Minimum probability compared to leading token to be considered |
| `presence_penalty?` | `number` \| ``null`` | (OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `preset?` | ``"problem_solving"`` \| ``"conversational"`` \| ``"fun"`` \| ``"prose"`` \| ``"creative"`` \| ``"business"`` \| ``"deterministic"`` \| ``"code"`` \| ``"multilingual"`` | Generation preset name (one of: problem_solving, conversational, fun, prose, creative, business, deterministic, code, multilingual) |
| `repetition_penalty?` | `number` \| ``null`` | (Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `temperature?` | `number` \| ``null`` | What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. |
| `top_p?` | `number` \| ``null`` | Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both. |

#### Defined in

[src/api/models/AgentDefaultSettings.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/AgentDefaultSettings.ts#L5)

___

### ChatInput

Ƭ **ChatInput**: [`ChatInputData`](api.md#chatinputdata) & [`ChatSettings`](api.md#chatsettings) & [`MemoryAccessOptions`](api.md#memoryaccessoptions)

#### Defined in

[src/api/models/ChatInput.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ChatInput.ts#L8)

___

### ChatInputData

Ƭ **ChatInputData**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `messages` | [`InputChatMLMessage`](api.md#inputchatmlmessage)[] | A list of new input messages comprising the conversation so far. |
| `tool_choice?` | [`ToolChoiceOption`](api.md#toolchoiceoption) \| [`NamedToolChoice`](api.md#namedtoolchoice) \| ``null`` | Can be one of existing tools given to the agent earlier or the ones included in the request |
| `tools?` | [`Tool`](api.md#tool)[] \| ``null`` | (Advanced) List of tools that are provided in addition to agent's default set of tools. Functions of same name in agent set are overriden |

#### Defined in

[src/api/models/ChatInputData.ts:9](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ChatInputData.ts#L9)

___

### ChatMLImageContentPart

Ƭ **ChatMLImageContentPart**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `image_url` | \{ `detail?`: ``"low"`` \| ``"high"`` \| ``"auto"`` ; `url`: `string`  } | Image content part, can be a URL or a base64-encoded image |
| `image_url.detail?` | ``"low"`` \| ``"high"`` \| ``"auto"`` | image detail to feed into the model can be low \| high \| auto |
| `image_url.url` | `string` | URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`) |
| `type` | ``"image_url"`` | Fixed to 'image_url' |

#### Defined in

[src/api/models/ChatMLImageContentPart.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ChatMLImageContentPart.ts#L5)

___

### ChatMLMessage

Ƭ **ChatMLMessage**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string` | ChatML content |
| `created_at` | `string` | Message created at (RFC-3339 format) |
| `id` | `string` | Message ID |
| `name?` | `string` | ChatML name |
| `role` | ``"user"`` \| ``"assistant"`` \| ``"system"`` \| ``"function_call"`` \| ``"function"`` | ChatML role (system\|assistant\|user\|function_call\|function) |

#### Defined in

[src/api/models/ChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ChatMLMessage.ts#L5)

___

### ChatMLTextContentPart

Ƭ **ChatMLTextContentPart**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `text` | `string` | Text content part |
| `type` | ``"text"`` | Fixed to 'text' |

#### Defined in

[src/api/models/ChatMLTextContentPart.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ChatMLTextContentPart.ts#L5)

___

### ChatResponse

Ƭ **ChatResponse**: `Object`

Represents a chat completion response returned by model, based on the provided input.

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `doc_ids` | [`DocIds`](api.md#docids) | - |
| `finish_reason` | ``"stop"`` \| ``"length"`` \| ``"tool_calls"`` \| ``"content_filter"`` \| ``"function_call"`` | The reason the model stopped generating tokens. This will be `stop` if the model hit a natural stop point or a provided stop sequence, `length` if the maximum number of tokens specified in the request was reached, `content_filter` if content was omitted due to a flag from our content filters, `tool_calls` if the model called a tool, or `function_call` (deprecated) if the model called a function. |
| `id` | `string` | A unique identifier for the chat completion. |
| `jobs?` | `string`[] | IDs (if any) of jobs created as part of this request |
| `response` | [`ChatMLMessage`](api.md#chatmlmessage)[][] | A list of chat completion messages produced as a response. |
| `usage` | [`CompletionUsage`](api.md#completionusage) | - |

#### Defined in

[src/api/models/ChatResponse.ts:11](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ChatResponse.ts#L11)

___

### ChatSettings

Ƭ **ChatSettings**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `frequency_penalty?` | `number` \| ``null`` | (OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `length_penalty?` | `number` \| ``null`` | (Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. |
| `logit_bias?` | `Record`\<`string`, `number`\> \| ``null`` | Modify the likelihood of specified tokens appearing in the completion. Accepts a JSON object that maps tokens (specified by their token ID in the tokenizer) to an associated bias value from -100 to 100. Mathematically, the bias is added to the logits generated by the model prior to sampling. The exact effect will vary per model, but values between -1 and 1 should decrease or increase likelihood of selection; values like -100 or 100 should result in a ban or exclusive selection of the relevant token. |
| `max_tokens?` | `number` \| ``null`` | The maximum number of tokens to generate in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length. |
| `min_p?` | `number` | Minimum probability compared to leading token to be considered |
| `presence_penalty?` | `number` \| ``null`` | (OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `preset?` | ``"problem_solving"`` \| ``"conversational"`` \| ``"fun"`` \| ``"prose"`` \| ``"creative"`` \| ``"business"`` \| ``"deterministic"`` \| ``"code"`` \| ``"multilingual"`` | Generation preset name (problem_solving\|conversational\|fun\|prose\|creative\|business\|deterministic\|code\|multilingual) |
| `repetition_penalty?` | `number` \| ``null`` | (Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim. |
| `response_format?` | \{ `pattern?`: `string` ; `schema?`: `any` ; `type?`: ``"text"`` \| ``"json_object"`` \| ``"regex"``  } | An object specifying the format that the model must output. Setting to `{ "type": "json_object" }` enables JSON mode, which guarantees the message the model generates is valid JSON. **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if `finish_reason="length"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length. |
| `response_format.pattern?` | `string` | Regular expression pattern to use if `type` is `"regex"` |
| `response_format.schema?` | `any` | JSON Schema to use if `type` is `"json_object"` |
| `response_format.type?` | ``"text"`` \| ``"json_object"`` \| ``"regex"`` | Must be one of `"text"`, `"regex"` or `"json_object"`. |
| `seed?` | `number` \| ``null`` | This feature is in Beta. If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result. Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend. |
| `stop?` | `string` \| ``null`` \| `string`[] | Up to 4 sequences where the API will stop generating further tokens. |
| `stream?` | `boolean` \| ``null`` | If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions). |
| `temperature?` | `number` \| ``null`` | What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. |
| `top_p?` | `number` \| ``null`` | Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. We generally recommend altering this or temperature but not both. |

#### Defined in

[src/api/models/ChatSettings.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ChatSettings.ts#L5)

___

### CompletionUsage

Ƭ **CompletionUsage**: `Object`

Usage statistics for the completion request.

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `completion_tokens` | `number` | Number of tokens in the generated completion. |
| `prompt_tokens` | `number` | Number of tokens in the prompt. |
| `total_tokens` | `number` | Total number of tokens used in the request (prompt + completion). |

#### Defined in

[src/api/models/CompletionUsage.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/CompletionUsage.ts#L8)

___

### CreateAgentRequest

Ƭ **CreateAgentRequest**: `Object`

A valid request payload for creating an agent

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the agent |
| `default_settings?` | [`AgentDefaultSettings`](api.md#agentdefaultsettings) | Default model settings to start every session with |
| `docs?` | [`CreateDoc`](api.md#createdoc)[] | List of docs about agent |
| `instructions?` | `string` \| `string`[] | Instructions for the agent |
| `metadata?` | `any` | (Optional) metadata |
| `model?` | `string` | Name of the model that the agent is supposed to use |
| `name` | `string` | Name of the agent |
| `tools?` | [`CreateToolRequest`](api.md#createtoolrequest)[] | A list of tools the model may call. Currently, only `function`s are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for. |

#### Defined in

[src/api/models/CreateAgentRequest.ts:11](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/CreateAgentRequest.ts#L11)

___

### CreateDoc

Ƭ **CreateDoc**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string`[] \| `string` | Information content |
| `metadata?` | `any` | Optional metadata |
| `title` | `string` | Title describing what this bit of information contains |

#### Defined in

[src/api/models/CreateDoc.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/CreateDoc.ts#L5)

___

### CreateSessionRequest

Ƭ **CreateSessionRequest**: `Object`

A valid request payload for creating a session

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `agent_id` | `string` | Agent ID of agent to associate with this session |
| `context_overflow?` | `string` | Action to start on context window overflow |
| `metadata?` | `any` | Optional metadata |
| `render_templates?` | `boolean` | Render system and assistant message content as jinja templates |
| `situation?` | `string` | A specific situation that sets the background for this session |
| `token_budget?` | `number` | Threshold value for the adaptive context functionality |
| `user_id?` | `string` | (Optional) User ID of user to associate with this session |

#### Defined in

[src/api/models/CreateSessionRequest.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/CreateSessionRequest.ts#L8)

___

### CreateToolRequest

Ƭ **CreateToolRequest**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | [`FunctionDef`](api.md#functiondef) | Function definition and parameters |
| `type` | ``"function"`` \| ``"webhook"`` | Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now) |

#### Defined in

[src/api/models/CreateToolRequest.ts:6](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/CreateToolRequest.ts#L6)

___

### CreateUserRequest

Ƭ **CreateUserRequest**: `Object`

A valid request payload for creating a user

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the user |
| `docs?` | [`CreateDoc`](api.md#createdoc)[] | List of docs about user |
| `metadata?` | `any` | (Optional) metadata |
| `name?` | `string` | Name of the user |

#### Defined in

[src/api/models/CreateUserRequest.ts:9](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/CreateUserRequest.ts#L9)

___

### Doc

Ƭ **Doc**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string`[] \| `string` | Information content |
| `created_at` | `string` | Doc created at |
| `id` | `string` | ID of doc |
| `metadata?` | `any` | optional metadata |
| `title` | `string` | Title describing what this bit of information contains |

#### Defined in

[src/api/models/Doc.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/Doc.ts#L5)

___

### DocIds

Ƭ **DocIds**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `agent_doc_ids` | `string`[] |
| `user_doc_ids` | `string`[] |

#### Defined in

[src/api/models/DocIds.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/DocIds.ts#L5)

___

### FunctionCallOption

Ƭ **FunctionCallOption**: `Object`

Specifying a particular function via `{"name": "my_function"}` forces the model to call that function.

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `name` | `string` | The name of the function to call. |

#### Defined in

[src/api/models/FunctionCallOption.ts:9](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/FunctionCallOption.ts#L9)

___

### FunctionDef

Ƭ **FunctionDef**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `description?` | `string` | A description of what the function does, used by the model to choose when and how to call the function. |
| `name` | `string` | The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64. |
| `parameters` | [`FunctionParameters`](api.md#functionparameters) | Parameters accepeted by this function |

#### Defined in

[src/api/models/FunctionDef.ts:6](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/FunctionDef.ts#L6)

___

### FunctionParameters

Ƭ **FunctionParameters**: `Record`\<`string`, `any`\>

The parameters the functions accepts, described as a JSON Schema object.

#### Defined in

[src/api/models/FunctionParameters.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/FunctionParameters.ts#L8)

___

### InputChatMLMessage

Ƭ **InputChatMLMessage**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string` | ChatML content |
| `continue?` | `boolean` | Whether to continue this message or return a new one |
| `name?` | `string` | ChatML name |
| `role` | ``"user"`` \| ``"assistant"`` \| ``"system"`` \| ``"function_call"`` \| ``"function"`` \| ``"auto"`` | ChatML role (system\|assistant\|user\|function_call\|function\|auto) |

#### Defined in

[src/api/models/InputChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/InputChatMLMessage.ts#L5)

___

### JobStatus

Ƭ **JobStatus**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `created_at` | `string` | Job created at (RFC-3339 format) |
| `has_progress?` | `boolean` | Whether this Job supports progress updates |
| `id` | `string` | Job id (UUID) |
| `name` | `string` | Name of the job |
| `progress?` | `number` | Progress percentage |
| `reason?` | `string` | Reason for current state |
| `state` | ``"pending"`` \| ``"in_progress"`` \| ``"retrying"`` \| ``"succeeded"`` \| ``"aborted"`` \| ``"failed"`` \| ``"unknown"`` | Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed) |
| `updated_at?` | `string` | Job updated at (RFC-3339 format) |

#### Defined in

[src/api/models/JobStatus.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/JobStatus.ts#L5)

___

### Memory

Ƭ **Memory**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `agent_id` | `string` | ID of the agent |
| `content` | `string` | Content of the memory |
| `created_at` | `string` | Memory created at (RFC-3339 format) |
| `entities` | `any`[] | List of entities mentioned in the memory |
| `id` | `string` | Memory id (UUID) |
| `last_accessed_at?` | `string` | Memory last accessed at (RFC-3339 format) |
| `sentiment?` | `number` | Sentiment (valence) of the memory on a scale of -1 to 1 |
| `timestamp?` | `string` | Memory happened at (RFC-3339 format) |
| `user_id` | `string` | ID of the user |

#### Defined in

[src/api/models/Memory.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/Memory.ts#L5)

___

### MemoryAccessOptions

Ƭ **MemoryAccessOptions**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `recall?` | `boolean` | Whether previous memories should be recalled or not |
| `record?` | `boolean` | Whether this interaction should be recorded in history or not |
| `remember?` | `boolean` | Whether this interaction should form memories or not |

#### Defined in

[src/api/models/MemoryAccessOptions.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/MemoryAccessOptions.ts#L5)

___

### NamedToolChoice

Ƭ **NamedToolChoice**: `Object`

Specifies a tool the model should use. Use to force the model to call a specific function.

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | \{ `name`: `string`  } | - |
| `function.name` | `string` | The name of the function to call. |
| `type` | ``"function"`` | The type of the tool. Currently, only `function` is supported. |

#### Defined in

[src/api/models/NamedToolChoice.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/NamedToolChoice.ts#L8)

___

### OpenAPIConfig

Ƭ **OpenAPIConfig**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `BASE` | `string` |
| `CREDENTIALS` | ``"include"`` \| ``"omit"`` \| ``"same-origin"`` |
| `ENCODE_PATH?` | (`path`: `string`) => `string` |
| `HEADERS?` | `Headers` \| `Resolver`\<`Headers`\> |
| `PASSWORD?` | `string` \| `Resolver`\<`string`\> |
| `TOKEN?` | `string` \| `Resolver`\<`string`\> |
| `USERNAME?` | `string` \| `Resolver`\<`string`\> |
| `VERSION` | `string` |
| `WITH_CREDENTIALS` | `boolean` |

#### Defined in

[src/api/core/OpenAPI.ts:10](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/core/OpenAPI.ts#L10)

___

### PartialFunctionDef

Ƭ **PartialFunctionDef**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `description?` | `string` | A description of what the function does, used by the model to choose when and how to call the function. |
| `name?` | `string` | The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64. |
| `parameters?` | [`FunctionParameters`](api.md#functionparameters) | Parameters accepeted by this function |

#### Defined in

[src/api/models/PartialFunctionDef.ts:6](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/PartialFunctionDef.ts#L6)

___

### PatchAgentRequest

Ƭ **PatchAgentRequest**: `Object`

A request for patching an agent

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the agent |
| `default_settings?` | [`AgentDefaultSettings`](api.md#agentdefaultsettings) | Default model settings to start every session with |
| `instructions?` | `string` \| `string`[] | Instructions for the agent |
| `metadata?` | `any` | Optional metadata |
| `model?` | `string` | Name of the model that the agent is supposed to use |
| `name?` | `string` | Name of the agent |

#### Defined in

[src/api/models/PatchAgentRequest.ts:9](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/PatchAgentRequest.ts#L9)

___

### PatchSessionRequest

Ƭ **PatchSessionRequest**: `Object`

A request for patching a session

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `context_overflow?` | `string` | Action to start on context window overflow |
| `metadata?` | `any` | Optional metadata |
| `situation?` | `string` | Updated situation for this session |
| `token_budget?` | `number` | Threshold value for the adaptive context functionality |

#### Defined in

[src/api/models/PatchSessionRequest.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/PatchSessionRequest.ts#L8)

___

### PatchToolRequest

Ƭ **PatchToolRequest**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | [`PartialFunctionDef`](api.md#partialfunctiondef) | Function definition and parameters |

#### Defined in

[src/api/models/PatchToolRequest.ts:6](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/PatchToolRequest.ts#L6)

___

### PatchUserRequest

Ƭ **PatchUserRequest**: `Object`

A request for patching a user

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the user |
| `metadata?` | `any` | Optional metadata |
| `name?` | `string` | Name of the user |

#### Defined in

[src/api/models/PatchUserRequest.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/PatchUserRequest.ts#L8)

___

### ResourceCreatedResponse

Ƭ **ResourceCreatedResponse**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `created_at` | `string` | - |
| `id` | `string` | - |
| `jobs?` | `string`[] | IDs (if any) of jobs created as part of this request |

#### Defined in

[src/api/models/ResourceCreatedResponse.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ResourceCreatedResponse.ts#L5)

___

### ResourceDeletedResponse

Ƭ **ResourceDeletedResponse**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `deleted_at` | `string` | - |
| `id` | `string` | - |
| `jobs?` | `string`[] | IDs (if any) of jobs created as part of this request |

#### Defined in

[src/api/models/ResourceDeletedResponse.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ResourceDeletedResponse.ts#L5)

___

### ResourceUpdatedResponse

Ƭ **ResourceUpdatedResponse**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `id` | `string` | - |
| `jobs?` | `string`[] | IDs (if any) of jobs created as part of this request |
| `updated_at` | `string` | - |

#### Defined in

[src/api/models/ResourceUpdatedResponse.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ResourceUpdatedResponse.ts#L5)

___

### Session

Ƭ **Session**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `agent_id` | `string` | Agent ID of agent associated with this session |
| `context_overflow?` | `string` | Action to start on context window overflow |
| `created_at?` | `string` | Session created at (RFC-3339 format) |
| `id` | `string` | Session id (UUID) |
| `metadata?` | `any` | Optional metadata |
| `render_templates?` | `boolean` | Render system and assistant message content as jinja templates |
| `situation?` | `string` | A specific situation that sets the background for this session |
| `summary?` | `string` | (null at the beginning) - generated automatically after every interaction |
| `token_budget?` | `number` | Threshold value for the adaptive context functionality |
| `updated_at?` | `string` | Session updated at (RFC-3339 format) |
| `user_id?` | `string` | User ID of user associated with this session |

#### Defined in

[src/api/models/Session.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/Session.ts#L5)

___

### Suggestion

Ƭ **Suggestion**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `content` | `string` | The content of the suggestion |
| `created_at?` | `string` | Suggestion created at (RFC-3339 format) |
| `message_id` | `string` | The message that produced it |
| `session_id` | `string` | Session this suggestion belongs to |
| `target` | ``"user"`` \| ``"agent"`` | Whether the suggestion is for the `agent` or a `user` |

#### Defined in

[src/api/models/Suggestion.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/Suggestion.ts#L5)

___

### Tool

Ƭ **Tool**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | [`FunctionDef`](api.md#functiondef) | Function definition and parameters |
| `id` | `string` | Tool ID |
| `type` | ``"function"`` \| ``"webhook"`` | Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now) |

#### Defined in

[src/api/models/Tool.ts:6](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/Tool.ts#L6)

___

### ToolChoiceOption

Ƭ **ToolChoiceOption**: ``"none"`` \| ``"auto"`` \| [`NamedToolChoice`](api.md#namedtoolchoice)

Controls which (if any) function is called by the model.
`none` means the model will not call a function and instead generates a message.
`auto` means the model can pick between generating a message or calling a function.
Specifying a particular function via `{"type: "function", "function": {"name": "my_function"}}` forces the model to call that function.

`none` is the default when no functions are present. `auto` is the default if functions are present.

#### Defined in

[src/api/models/ToolChoiceOption.ts:15](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/ToolChoiceOption.ts#L15)

___

### UpdateAgentRequest

Ƭ **UpdateAgentRequest**: `Object`

A valid request payload for updating an agent

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about` | `string` | About the agent |
| `default_settings?` | [`AgentDefaultSettings`](api.md#agentdefaultsettings) | Default model settings to start every session with |
| `instructions?` | `string` \| `string`[] | Instructions for the agent |
| `metadata?` | `any` | Optional metadata |
| `model?` | `string` | Name of the model that the agent is supposed to use |
| `name` | `string` | Name of the agent |

#### Defined in

[src/api/models/UpdateAgentRequest.ts:9](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/UpdateAgentRequest.ts#L9)

___

### UpdateSessionRequest

Ƭ **UpdateSessionRequest**: `Object`

A valid request payload for updating a session

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `context_overflow?` | `string` | Action to start on context window overflow |
| `metadata?` | `any` | Optional metadata |
| `situation` | `string` | Updated situation for this session |
| `token_budget?` | `number` | Threshold value for the adaptive context functionality |

#### Defined in

[src/api/models/UpdateSessionRequest.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/UpdateSessionRequest.ts#L8)

___

### UpdateToolRequest

Ƭ **UpdateToolRequest**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | [`FunctionDef`](api.md#functiondef) | Function definition and parameters |

#### Defined in

[src/api/models/UpdateToolRequest.ts:6](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/UpdateToolRequest.ts#L6)

___

### UpdateUserRequest

Ƭ **UpdateUserRequest**: `Object`

A valid request payload for updating a user

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about` | `string` | About the user |
| `metadata?` | `any` | Optional metadata |
| `name` | `string` | Name of the user |

#### Defined in

[src/api/models/UpdateUserRequest.ts:8](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/UpdateUserRequest.ts#L8)

___

### User

Ƭ **User**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `about?` | `string` | About the user |
| `created_at?` | `string` | User created at (RFC-3339 format) |
| `id` | `string` | User id (UUID) |
| `metadata?` | `any` | (Optional) metadata |
| `name?` | `string` | Name of the user |
| `updated_at?` | `string` | User updated at (RFC-3339 format) |

#### Defined in

[src/api/models/User.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/User.ts#L5)

___

### agent\_id

Ƭ **agent\_id**: `string`

#### Defined in

[src/api/models/agent_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/agent_id.ts#L5)

___

### doc\_id

Ƭ **doc\_id**: `string`

#### Defined in

[src/api/models/doc_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/doc_id.ts#L5)

___

### job\_id

Ƭ **job\_id**: `string`

#### Defined in

[src/api/models/job_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/job_id.ts#L5)

___

### memory\_id

Ƭ **memory\_id**: `string`

#### Defined in

[src/api/models/memory_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/memory_id.ts#L5)

___

### message\_id

Ƭ **message\_id**: `string`

#### Defined in

[src/api/models/message_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/message_id.ts#L5)

___

### session\_id

Ƭ **session\_id**: `string`

#### Defined in

[src/api/models/session_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/session_id.ts#L5)

___

### tool\_id

Ƭ **tool\_id**: `string`

#### Defined in

[src/api/models/tool_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/tool_id.ts#L5)

___

### user\_id

Ƭ **user\_id**: `string`

#### Defined in

[src/api/models/user_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/models/user_id.ts#L5)

## Variables

### $Agent

• `Const` **$Agent**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `about`: \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Agent created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `default_settings`: \{ `description`: ``"Default settings for all sessions created by this agent"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } ; `id`: \{ `description`: ``"Agent id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `instructions`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `model`: \{ `description`: ``"The model to use with this agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `updated_at`: \{ `description`: ``"Agent updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the agent"`` |
| `properties.about.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Agent created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Agent created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.default_settings` | \{ `description`: ``"Default settings for all sessions created by this agent"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } |
| `properties.default_settings.description` | ``"Default settings for all sessions created by this agent"`` |
| `properties.default_settings.type` | ``"AgentDefaultSettings"`` |
| `properties.id` | \{ `description`: ``"Agent id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Agent id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.instructions` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.instructions.contains` | readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.instructions.description` | ``"Instructions for the agent"`` |
| `properties.instructions.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.model` | \{ `description`: ``"The model to use with this agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.model.description` | ``"The model to use with this agent"`` |
| `properties.model.isRequired` | ``true`` |
| `properties.model.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the agent"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.updated_at` | \{ `description`: ``"Agent updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"Agent updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Agent.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$Agent.ts#L5)

___

### $AgentDefaultSettings

• `Const` **$AgentDefaultSettings**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `frequency_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `minimum`: ``-2`` = -2; `type`: ``"number"`` = "number" } ; `length_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `min_p`: \{ `description`: ``"Minimum probability compared to leading token to be considered"`` ; `exclusiveMaximum`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } ; `presence_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `preset`: \{ `type`: ``"Enum"`` = "Enum" } ; `repetition_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `temperature`: \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``3`` = 3; `type`: ``"number"`` = "number" } ; `top_p`: \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" }  } |
| `properties.frequency_penalty` | \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `minimum`: ``-2`` = -2; `type`: ``"number"`` = "number" } |
| `properties.frequency_penalty.description` | ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.frequency_penalty.isNullable` | ``true`` |
| `properties.frequency_penalty.maximum` | ``2`` |
| `properties.frequency_penalty.minimum` | ``-2`` |
| `properties.frequency_penalty.type` | ``"number"`` |
| `properties.length_penalty` | \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.length_penalty.description` | ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` |
| `properties.length_penalty.isNullable` | ``true`` |
| `properties.length_penalty.maximum` | ``2`` |
| `properties.length_penalty.type` | ``"number"`` |
| `properties.min_p` | \{ `description`: ``"Minimum probability compared to leading token to be considered"`` ; `exclusiveMaximum`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.min_p.description` | ``"Minimum probability compared to leading token to be considered"`` |
| `properties.min_p.exclusiveMaximum` | ``true`` |
| `properties.min_p.maximum` | ``1`` |
| `properties.min_p.type` | ``"number"`` |
| `properties.presence_penalty` | \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.presence_penalty.description` | ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.presence_penalty.isNullable` | ``true`` |
| `properties.presence_penalty.maximum` | ``1`` |
| `properties.presence_penalty.minimum` | ``-1`` |
| `properties.presence_penalty.type` | ``"number"`` |
| `properties.preset` | \{ `type`: ``"Enum"`` = "Enum" } |
| `properties.preset.type` | ``"Enum"`` |
| `properties.repetition_penalty` | \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.repetition_penalty.description` | ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.repetition_penalty.isNullable` | ``true`` |
| `properties.repetition_penalty.maximum` | ``2`` |
| `properties.repetition_penalty.type` | ``"number"`` |
| `properties.temperature` | \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``3`` = 3; `type`: ``"number"`` = "number" } |
| `properties.temperature.description` | ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` |
| `properties.temperature.isNullable` | ``true`` |
| `properties.temperature.maximum` | ``3`` |
| `properties.temperature.type` | ``"number"`` |
| `properties.top_p` | \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.top_p.description` | ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` |
| `properties.top_p.isNullable` | ``true`` |
| `properties.top_p.maximum` | ``1`` |
| `properties.top_p.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$AgentDefaultSettings.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$AgentDefaultSettings.ts#L5)

___

### $ChatInput

• `Const` **$ChatInput**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `contains` | readonly [\{ `type`: ``"ChatInputData"`` = "ChatInputData" }, \{ `type`: ``"ChatSettings"`` = "ChatSettings" }, \{ `type`: ``"MemoryAccessOptions"`` = "MemoryAccessOptions" }] |
| `type` | ``"all-of"`` |

#### Defined in

[src/api/schemas/$ChatInput.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ChatInput.ts#L5)

___

### $ChatInputData

• `Const` **$ChatInputData**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `messages`: \{ `contains`: \{ `type`: ``"InputChatMLMessage"`` = "InputChatMLMessage" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `tool_choice`: \{ `contains`: readonly [\{ `type`: ``"ToolChoiceOption"`` = "ToolChoiceOption" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] ; `description`: ``"Can be one of existing tools given to the agent earlier or the ones included in the request"`` ; `isNullable`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `tools`: \{ `contains`: \{ `type`: ``"Tool"`` = "Tool" } ; `isNullable`: ``true`` = true; `type`: ``"array"`` = "array" }  } |
| `properties.messages` | \{ `contains`: \{ `type`: ``"InputChatMLMessage"`` = "InputChatMLMessage" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.messages.contains` | \{ `type`: ``"InputChatMLMessage"`` = "InputChatMLMessage" } |
| `properties.messages.contains.type` | ``"InputChatMLMessage"`` |
| `properties.messages.isRequired` | ``true`` |
| `properties.messages.type` | ``"array"`` |
| `properties.tool_choice` | \{ `contains`: readonly [\{ `type`: ``"ToolChoiceOption"`` = "ToolChoiceOption" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] ; `description`: ``"Can be one of existing tools given to the agent earlier or the ones included in the request"`` ; `isNullable`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.tool_choice.contains` | readonly [\{ `type`: ``"ToolChoiceOption"`` = "ToolChoiceOption" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] |
| `properties.tool_choice.description` | ``"Can be one of existing tools given to the agent earlier or the ones included in the request"`` |
| `properties.tool_choice.isNullable` | ``true`` |
| `properties.tool_choice.type` | ``"one-of"`` |
| `properties.tools` | \{ `contains`: \{ `type`: ``"Tool"`` = "Tool" } ; `isNullable`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.tools.contains` | \{ `type`: ``"Tool"`` = "Tool" } |
| `properties.tools.contains.type` | ``"Tool"`` |
| `properties.tools.isNullable` | ``true`` |
| `properties.tools.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$ChatInputData.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ChatInputData.ts#L5)

___

### $ChatMLImageContentPart

• `Const` **$ChatMLImageContentPart**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `image_url`: \{ `description`: ``"Image content part, can be a URL or a base64-encoded image"`` ; `isRequired`: ``true`` = true; `properties`: \{ `detail`: \{ `type`: ``"Enum"`` = "Enum" } ; `url`: \{ `description`: ``"URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  }  } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.image_url` | \{ `description`: ``"Image content part, can be a URL or a base64-encoded image"`` ; `isRequired`: ``true`` = true; `properties`: \{ `detail`: \{ `type`: ``"Enum"`` = "Enum" } ; `url`: \{ `description`: ``"URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  }  } |
| `properties.image_url.description` | ``"Image content part, can be a URL or a base64-encoded image"`` |
| `properties.image_url.isRequired` | ``true`` |
| `properties.image_url.properties` | \{ `detail`: \{ `type`: ``"Enum"`` = "Enum" } ; `url`: \{ `description`: ``"URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.image_url.properties.detail` | \{ `type`: ``"Enum"`` = "Enum" } |
| `properties.image_url.properties.detail.type` | ``"Enum"`` |
| `properties.image_url.properties.url` | \{ `description`: ``"URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.image_url.properties.url.description` | ``"URL or base64 data url (e.g. `data:image/jpeg;base64,<the base64 encoded image>`)"`` |
| `properties.image_url.properties.url.isRequired` | ``true`` |
| `properties.image_url.properties.url.type` | ``"string"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$ChatMLImageContentPart.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ChatMLImageContentPart.ts#L5)

___

### $ChatMLMessage

• `Const` **$ChatMLMessage**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }] ; `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `created_at`: \{ `description`: ``"Message created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"Message ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"ChatML name"`` ; `type`: ``"string"`` = "string" } ; `role`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.content` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }] ; `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.content.contains` | readonly [\{ `type`: ``"string"`` = "string" }] |
| `properties.content.description` | ``"ChatML content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"one-of"`` |
| `properties.created_at` | \{ `description`: ``"Message created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Message created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"Message ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Message ID"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"ChatML name"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"ChatML name"`` |
| `properties.name.type` | ``"string"`` |
| `properties.role` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.role.isRequired` | ``true`` |
| `properties.role.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$ChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ChatMLMessage.ts#L5)

___

### $ChatMLTextContentPart

• `Const` **$ChatMLTextContentPart**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `text`: \{ `description`: ``"Text content part"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.text` | \{ `description`: ``"Text content part"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.text.description` | ``"Text content part"`` |
| `properties.text.isRequired` | ``true`` |
| `properties.text.type` | ``"string"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$ChatMLTextContentPart.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ChatMLTextContentPart.ts#L5)

___

### $ChatResponse

• `Const` **$ChatResponse**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Represents a chat completion response returned by model, based on the provided input."`` |
| `properties` | \{ `doc_ids`: \{ `isRequired`: ``true`` = true; `type`: ``"DocIds"`` = "DocIds" } ; `finish_reason`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } ; `id`: \{ `description`: ``"A unique identifier for the chat completion."`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `jobs`: \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } ; `response`: \{ `contains`: \{ `contains`: \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } ; `type`: ``"array"`` = "array" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `usage`: \{ `isRequired`: ``true`` = true; `type`: ``"CompletionUsage"`` = "CompletionUsage" }  } |
| `properties.doc_ids` | \{ `isRequired`: ``true`` = true; `type`: ``"DocIds"`` = "DocIds" } |
| `properties.doc_ids.isRequired` | ``true`` |
| `properties.doc_ids.type` | ``"DocIds"`` |
| `properties.finish_reason` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.finish_reason.isRequired` | ``true`` |
| `properties.finish_reason.type` | ``"Enum"`` |
| `properties.id` | \{ `description`: ``"A unique identifier for the chat completion."`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"A unique identifier for the chat completion."`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.jobs` | \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } |
| `properties.jobs.contains` | \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.jobs.contains.format` | ``"uuid"`` |
| `properties.jobs.contains.type` | ``"string"`` |
| `properties.jobs.type` | ``"array"`` |
| `properties.response` | \{ `contains`: \{ `contains`: \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } ; `type`: ``"array"`` = "array" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.response.contains` | \{ `contains`: \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } ; `type`: ``"array"`` = "array" } |
| `properties.response.contains.contains` | \{ `type`: ``"ChatMLMessage"`` = "ChatMLMessage" } |
| `properties.response.contains.contains.type` | ``"ChatMLMessage"`` |
| `properties.response.contains.type` | ``"array"`` |
| `properties.response.isRequired` | ``true`` |
| `properties.response.type` | ``"array"`` |
| `properties.usage` | \{ `isRequired`: ``true`` = true; `type`: ``"CompletionUsage"`` = "CompletionUsage" } |
| `properties.usage.isRequired` | ``true`` |
| `properties.usage.type` | ``"CompletionUsage"`` |

#### Defined in

[src/api/schemas/$ChatResponse.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ChatResponse.ts#L5)

___

### $ChatSettings

• `Const` **$ChatSettings**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `frequency_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `length_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `logit_bias`: \{ `contains`: \{ `type`: ``"number"`` = "number" } ; `isNullable`: ``true`` = true; `type`: ``"dictionary"`` = "dictionary" } ; `max_tokens`: \{ `description`: ``"The maximum number of tokens to generate in the chat completion.\n      The total length of input tokens and generated tokens is limited by the model's context length.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``16384`` = 16384; `minimum`: ``1`` = 1; `type`: ``"number"`` = "number" } ; `min_p`: \{ `description`: ``"Minimum probability compared to leading token to be considered"`` ; `exclusiveMaximum`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } ; `presence_penalty`: \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `preset`: \{ `type`: ``"Enum"`` = "Enum" } ; `repetition_penalty`: \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `response_format`: \{ `description`: ``"An object specifying the format that the model must output.\n      Setting to `{ \"type\": \"json_object\" }` enables JSON mode, which guarantees the message the model generates is valid JSON.\n       **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly \"stuck\" request. Also note that the message content may be partially cut off if `finish_reason=\"length\"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.\n      "`` ; `properties`: \{ `pattern`: \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } ; `schema`: \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } ; `type`: \{ `type`: ``"Enum"`` = "Enum" }  }  } ; `seed`: \{ `description`: ``"This feature is in Beta.\n      If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result.\n      Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``9999`` = 9999; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `stop`: \{ `contains`: readonly [\{ `isNullable`: ``true`` = true; `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Up to 4 sequences where the API will stop generating further tokens.\n      "`` ; `type`: ``"one-of"`` = "one-of" } ; `stream`: \{ `description`: ``"If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).\n      "`` ; `isNullable`: ``true`` = true; `type`: ``"boolean"`` = "boolean" } ; `temperature`: \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } ; `top_p`: \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `exclusiveMinimum`: ``true`` = true; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" }  } |
| `properties.frequency_penalty` | \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.frequency_penalty.description` | ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.frequency_penalty.isNullable` | ``true`` |
| `properties.frequency_penalty.maximum` | ``1`` |
| `properties.frequency_penalty.minimum` | ``-1`` |
| `properties.frequency_penalty.type` | ``"number"`` |
| `properties.length_penalty` | \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.length_penalty.description` | ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize number of tokens generated. "`` |
| `properties.length_penalty.isNullable` | ``true`` |
| `properties.length_penalty.maximum` | ``2`` |
| `properties.length_penalty.type` | ``"number"`` |
| `properties.logit_bias` | \{ `contains`: \{ `type`: ``"number"`` = "number" } ; `isNullable`: ``true`` = true; `type`: ``"dictionary"`` = "dictionary" } |
| `properties.logit_bias.contains` | \{ `type`: ``"number"`` = "number" } |
| `properties.logit_bias.contains.type` | ``"number"`` |
| `properties.logit_bias.isNullable` | ``true`` |
| `properties.logit_bias.type` | ``"dictionary"`` |
| `properties.max_tokens` | \{ `description`: ``"The maximum number of tokens to generate in the chat completion.\n      The total length of input tokens and generated tokens is limited by the model's context length.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``16384`` = 16384; `minimum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.max_tokens.description` | ``"The maximum number of tokens to generate in the chat completion.\n      The total length of input tokens and generated tokens is limited by the model's context length.\n      "`` |
| `properties.max_tokens.isNullable` | ``true`` |
| `properties.max_tokens.maximum` | ``16384`` |
| `properties.max_tokens.minimum` | ``1`` |
| `properties.max_tokens.type` | ``"number"`` |
| `properties.min_p` | \{ `description`: ``"Minimum probability compared to leading token to be considered"`` ; `exclusiveMaximum`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.min_p.description` | ``"Minimum probability compared to leading token to be considered"`` |
| `properties.min_p.exclusiveMaximum` | ``true`` |
| `properties.min_p.maximum` | ``1`` |
| `properties.min_p.type` | ``"number"`` |
| `properties.presence_penalty` | \{ `description`: ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.presence_penalty.description` | ``"(OpenAI-like) Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.presence_penalty.isNullable` | ``true`` |
| `properties.presence_penalty.maximum` | ``1`` |
| `properties.presence_penalty.minimum` | ``-1`` |
| `properties.presence_penalty.type` | ``"number"`` |
| `properties.preset` | \{ `type`: ``"Enum"`` = "Enum" } |
| `properties.preset.type` | ``"Enum"`` |
| `properties.repetition_penalty` | \{ `description`: ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.repetition_penalty.description` | ``"(Huggingface-like) Number between 0 and 2.0. 1.0 is neutral and values larger than that penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim."`` |
| `properties.repetition_penalty.isNullable` | ``true`` |
| `properties.repetition_penalty.maximum` | ``2`` |
| `properties.repetition_penalty.type` | ``"number"`` |
| `properties.response_format` | \{ `description`: ``"An object specifying the format that the model must output.\n      Setting to `{ \"type\": \"json_object\" }` enables JSON mode, which guarantees the message the model generates is valid JSON.\n       **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly \"stuck\" request. Also note that the message content may be partially cut off if `finish_reason=\"length\"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.\n      "`` ; `properties`: \{ `pattern`: \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } ; `schema`: \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } ; `type`: \{ `type`: ``"Enum"`` = "Enum" }  }  } |
| `properties.response_format.description` | ``"An object specifying the format that the model must output.\n      Setting to `{ \"type\": \"json_object\" }` enables JSON mode, which guarantees the message the model generates is valid JSON.\n       **Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly \"stuck\" request. Also note that the message content may be partially cut off if `finish_reason=\"length\"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length.\n      "`` |
| `properties.response_format.properties` | \{ `pattern`: \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } ; `schema`: \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } ; `type`: \{ `type`: ``"Enum"`` = "Enum" }  } |
| `properties.response_format.properties.pattern` | \{ `description`: ``"Regular expression pattern to use if `type` is `\"regex\"`"`` ; `type`: ``"string"`` = "string" } |
| `properties.response_format.properties.pattern.description` | ``"Regular expression pattern to use if `type` is `\"regex\"`"`` |
| `properties.response_format.properties.pattern.type` | ``"string"`` |
| `properties.response_format.properties.schema` | \{ `description`: ``"JSON Schema to use if `type` is `\"json_object\"`"`` ; `properties`: {} = \{} } |
| `properties.response_format.properties.schema.description` | ``"JSON Schema to use if `type` is `\"json_object\"`"`` |
| `properties.response_format.properties.schema.properties` | {} |
| `properties.response_format.properties.type` | \{ `type`: ``"Enum"`` = "Enum" } |
| `properties.response_format.properties.type.type` | ``"Enum"`` |
| `properties.seed` | \{ `description`: ``"This feature is in Beta.\n      If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result.\n      Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.\n      "`` ; `isNullable`: ``true`` = true; `maximum`: ``9999`` = 9999; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.seed.description` | ``"This feature is in Beta.\n      If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same `seed` and parameters should return the same result.\n      Determinism is not guaranteed, and you should refer to the `system_fingerprint` response parameter to monitor changes in the backend.\n      "`` |
| `properties.seed.isNullable` | ``true`` |
| `properties.seed.maximum` | ``9999`` |
| `properties.seed.minimum` | ``-1`` |
| `properties.seed.type` | ``"number"`` |
| `properties.stop` | \{ `contains`: readonly [\{ `isNullable`: ``true`` = true; `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Up to 4 sequences where the API will stop generating further tokens.\n      "`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.stop.contains` | readonly [\{ `isNullable`: ``true`` = true; `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.stop.description` | ``"Up to 4 sequences where the API will stop generating further tokens.\n      "`` |
| `properties.stop.type` | ``"one-of"`` |
| `properties.stream` | \{ `description`: ``"If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).\n      "`` ; `isNullable`: ``true`` = true; `type`: ``"boolean"`` = "boolean" } |
| `properties.stream.description` | ``"If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format) as they become available, with the stream terminated by a `data: [DONE]` message. [Example Python code](https://cookbook.openai.com/examples/how_to_stream_completions).\n      "`` |
| `properties.stream.isNullable` | ``true`` |
| `properties.stream.type` | ``"boolean"`` |
| `properties.temperature` | \{ `description`: ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` ; `isNullable`: ``true`` = true; `maximum`: ``2`` = 2; `type`: ``"number"`` = "number" } |
| `properties.temperature.description` | ``"What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic."`` |
| `properties.temperature.isNullable` | ``true`` |
| `properties.temperature.maximum` | ``2`` |
| `properties.temperature.type` | ``"number"`` |
| `properties.top_p` | \{ `description`: ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` ; `exclusiveMinimum`: ``true`` = true; `isNullable`: ``true`` = true; `maximum`: ``1`` = 1; `type`: ``"number"`` = "number" } |
| `properties.top_p.description` | ``"Defaults to 1 An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.  We generally recommend altering this or temperature but not both."`` |
| `properties.top_p.exclusiveMinimum` | ``true`` |
| `properties.top_p.isNullable` | ``true`` |
| `properties.top_p.maximum` | ``1`` |
| `properties.top_p.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$ChatSettings.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ChatSettings.ts#L5)

___

### $CompletionUsage

• `Const` **$CompletionUsage**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Usage statistics for the completion request."`` |
| `properties` | \{ `completion_tokens`: \{ `description`: ``"Number of tokens in the generated completion."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } ; `prompt_tokens`: \{ `description`: ``"Number of tokens in the prompt."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } ; `total_tokens`: \{ `description`: ``"Total number of tokens used in the request (prompt + completion)."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" }  } |
| `properties.completion_tokens` | \{ `description`: ``"Number of tokens in the generated completion."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } |
| `properties.completion_tokens.description` | ``"Number of tokens in the generated completion."`` |
| `properties.completion_tokens.isRequired` | ``true`` |
| `properties.completion_tokens.type` | ``"number"`` |
| `properties.prompt_tokens` | \{ `description`: ``"Number of tokens in the prompt."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } |
| `properties.prompt_tokens.description` | ``"Number of tokens in the prompt."`` |
| `properties.prompt_tokens.isRequired` | ``true`` |
| `properties.prompt_tokens.type` | ``"number"`` |
| `properties.total_tokens` | \{ `description`: ``"Total number of tokens used in the request (prompt + completion)."`` ; `isRequired`: ``true`` = true; `type`: ``"number"`` = "number" } |
| `properties.total_tokens.description` | ``"Total number of tokens used in the request (prompt + completion)."`` |
| `properties.total_tokens.isRequired` | ``true`` |
| `properties.total_tokens.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$CompletionUsage.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$CompletionUsage.ts#L5)

___

### $CreateAgentRequest

• `Const` **$CreateAgentRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for creating an agent"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } ; `default_settings`: \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } ; `docs`: \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } ; `instructions`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } ; `model`: \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `tools`: \{ `contains`: \{ `type`: ``"CreateToolRequest"`` = "CreateToolRequest" } ; `type`: ``"array"`` = "array" }  } |
| `properties.about` | \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the agent"`` |
| `properties.about.type` | ``"string"`` |
| `properties.default_settings` | \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } |
| `properties.default_settings.description` | ``"Default model settings to start every session with"`` |
| `properties.default_settings.type` | ``"AgentDefaultSettings"`` |
| `properties.docs` | \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } |
| `properties.docs.contains` | \{ `type`: ``"CreateDoc"`` = "CreateDoc" } |
| `properties.docs.contains.type` | ``"CreateDoc"`` |
| `properties.docs.type` | ``"array"`` |
| `properties.instructions` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.instructions.contains` | readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.instructions.description` | ``"Instructions for the agent"`` |
| `properties.instructions.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"(Optional) metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.model` | \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } |
| `properties.model.description` | ``"Name of the model that the agent is supposed to use"`` |
| `properties.model.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the agent"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.tools` | \{ `contains`: \{ `type`: ``"CreateToolRequest"`` = "CreateToolRequest" } ; `type`: ``"array"`` = "array" } |
| `properties.tools.contains` | \{ `type`: ``"CreateToolRequest"`` = "CreateToolRequest" } |
| `properties.tools.contains.type` | ``"CreateToolRequest"`` |
| `properties.tools.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$CreateAgentRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$CreateAgentRequest.ts#L5)

___

### $CreateDoc

• `Const` **$CreateDoc**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `title`: \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.content` | \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.content.contains` | readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] |
| `properties.content.description` | ``"Information content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.title` | \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.title.description` | ``"Title describing what this bit of information contains"`` |
| `properties.title.isRequired` | ``true`` |
| `properties.title.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$CreateDoc.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$CreateDoc.ts#L5)

___

### $CreateSessionRequest

• `Const` **$CreateSessionRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for creating a session"`` |
| `properties` | \{ `agent_id`: \{ `description`: ``"Agent ID of agent to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `context_overflow`: \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `render_templates`: \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } ; `situation`: \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } ; `token_budget`: \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" } ; `user_id`: \{ `description`: ``"(Optional) User ID of user to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" }  } |
| `properties.agent_id` | \{ `description`: ``"Agent ID of agent to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.agent_id.description` | ``"Agent ID of agent to associate with this session"`` |
| `properties.agent_id.format` | ``"uuid"`` |
| `properties.agent_id.isRequired` | ``true`` |
| `properties.agent_id.type` | ``"string"`` |
| `properties.context_overflow` | \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } |
| `properties.context_overflow.description` | ``"Action to start on context window overflow"`` |
| `properties.context_overflow.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.render_templates` | \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.render_templates.description` | ``"Render system and assistant message content as jinja templates"`` |
| `properties.render_templates.type` | ``"boolean"`` |
| `properties.situation` | \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"A specific situation that sets the background for this session"`` |
| `properties.situation.type` | ``"string"`` |
| `properties.token_budget` | \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" } |
| `properties.token_budget.description` | ``"Threshold value for the adaptive context functionality"`` |
| `properties.token_budget.type` | ``"number"`` |
| `properties.user_id` | \{ `description`: ``"(Optional) User ID of user to associate with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.user_id.description` | ``"(Optional) User ID of user to associate with this session"`` |
| `properties.user_id.format` | ``"uuid"`` |
| `properties.user_id.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$CreateSessionRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$CreateSessionRequest.ts#L5)

___

### $CreateToolRequest

• `Const` **$CreateToolRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `function`: \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.function` | \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.function.contains` | readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] |
| `properties.function.description` | ``"Function definition and parameters"`` |
| `properties.function.isRequired` | ``true`` |
| `properties.function.type` | ``"one-of"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$CreateToolRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$CreateToolRequest.ts#L5)

___

### $CreateUserRequest

• `Const` **$CreateUserRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for creating a user"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } ; `docs`: \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } ; `metadata`: \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.type` | ``"string"`` |
| `properties.docs` | \{ `contains`: \{ `type`: ``"CreateDoc"`` = "CreateDoc" } ; `type`: ``"array"`` = "array" } |
| `properties.docs.contains` | \{ `type`: ``"CreateDoc"`` = "CreateDoc" } |
| `properties.docs.contains.type` | ``"CreateDoc"`` |
| `properties.docs.type` | ``"array"`` |
| `properties.metadata` | \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"(Optional) metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$CreateUserRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$CreateUserRequest.ts#L5)

___

### $Doc

• `Const` **$Doc**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `created_at`: \{ `description`: ``"Doc created at"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"ID of doc"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"optional metadata"`` ; `properties`: {} = \{} } ; `title`: \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.content` | \{ `contains`: readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] ; `description`: ``"Information content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.content.contains` | readonly [\{ `contains`: \{ `minItems`: ``1`` = 1; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }, \{ `description`: ``"A single document chunk"`` ; `type`: ``"string"`` = "string" }] |
| `properties.content.description` | ``"Information content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"one-of"`` |
| `properties.created_at` | \{ `description`: ``"Doc created at"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Doc created at"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"ID of doc"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"ID of doc"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.title` | \{ `description`: ``"Title describing what this bit of information contains"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.title.description` | ``"Title describing what this bit of information contains"`` |
| `properties.title.isRequired` | ``true`` |
| `properties.title.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Doc.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$Doc.ts#L5)

___

### $DocIds

• `Const` **$DocIds**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `agent_doc_ids`: \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `user_doc_ids`: \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" }  } |
| `properties.agent_doc_ids` | \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.agent_doc_ids.contains` | \{ `type`: ``"string"`` = "string" } |
| `properties.agent_doc_ids.contains.type` | ``"string"`` |
| `properties.agent_doc_ids.isRequired` | ``true`` |
| `properties.agent_doc_ids.type` | ``"array"`` |
| `properties.user_doc_ids` | \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.user_doc_ids.contains` | \{ `type`: ``"string"`` = "string" } |
| `properties.user_doc_ids.contains.type` | ``"string"`` |
| `properties.user_doc_ids.isRequired` | ``true`` |
| `properties.user_doc_ids.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$DocIds.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$DocIds.ts#L5)

___

### $FunctionCallOption

• `Const` **$FunctionCallOption**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Specifying a particular function via `{\"name\": \"my_function\"}` forces the model to call that function.\n  "`` |
| `properties` | \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.name` | \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"The name of the function to call."`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$FunctionCallOption.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$FunctionCallOption.ts#L5)

___

### $FunctionDef

• `Const` **$FunctionDef**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `description`: \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `parameters`: \{ `description`: ``"Parameters accepeted by this function"`` ; `isRequired`: ``true`` = true; `type`: ``"FunctionParameters"`` = "FunctionParameters" }  } |
| `properties.description` | \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } |
| `properties.description.description` | ``"A description of what the function does, used by the model to choose when and how to call the function."`` |
| `properties.description.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.parameters` | \{ `description`: ``"Parameters accepeted by this function"`` ; `isRequired`: ``true`` = true; `type`: ``"FunctionParameters"`` = "FunctionParameters" } |
| `properties.parameters.description` | ``"Parameters accepeted by this function"`` |
| `properties.parameters.isRequired` | ``true`` |
| `properties.parameters.type` | ``"FunctionParameters"`` |

#### Defined in

[src/api/schemas/$FunctionDef.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$FunctionDef.ts#L5)

___

### $FunctionParameters

• `Const` **$FunctionParameters**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `contains` | \{ `properties`: {} = \{} } |
| `contains.properties` | {} |
| `type` | ``"dictionary"`` |

#### Defined in

[src/api/schemas/$FunctionParameters.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$FunctionParameters.ts#L5)

___

### $InputChatMLMessage

• `Const` **$InputChatMLMessage**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }] ; `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `continue`: \{ `description`: ``"Whether to continue this message or return a new one"`` ; `type`: ``"boolean"`` = "boolean" } ; `name`: \{ `description`: ``"ChatML name"`` ; `type`: ``"string"`` = "string" } ; `role`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.content` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }] ; `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.content.contains` | readonly [\{ `type`: ``"string"`` = "string" }] |
| `properties.content.description` | ``"ChatML content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"one-of"`` |
| `properties.continue` | \{ `description`: ``"Whether to continue this message or return a new one"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.continue.description` | ``"Whether to continue this message or return a new one"`` |
| `properties.continue.type` | ``"boolean"`` |
| `properties.name` | \{ `description`: ``"ChatML name"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"ChatML name"`` |
| `properties.name.type` | ``"string"`` |
| `properties.role` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.role.isRequired` | ``true`` |
| `properties.role.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$InputChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$InputChatMLMessage.ts#L5)

___

### $JobStatus

• `Const` **$JobStatus**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `created_at`: \{ `description`: ``"Job created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `has_progress`: \{ `description`: ``"Whether this Job supports progress updates"`` ; `type`: ``"boolean"`` = "boolean" } ; `id`: \{ `description`: ``"Job id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the job"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `progress`: \{ `description`: ``"Progress percentage"`` ; `maximum`: ``100`` = 100; `type`: ``"number"`` = "number" } ; `reason`: \{ `description`: ``"Reason for current state"`` ; `type`: ``"string"`` = "string" } ; `state`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } ; `updated_at`: \{ `description`: ``"Job updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" }  } |
| `properties.created_at` | \{ `description`: ``"Job created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Job created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.has_progress` | \{ `description`: ``"Whether this Job supports progress updates"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.has_progress.description` | ``"Whether this Job supports progress updates"`` |
| `properties.has_progress.type` | ``"boolean"`` |
| `properties.id` | \{ `description`: ``"Job id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Job id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the job"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the job"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |
| `properties.progress` | \{ `description`: ``"Progress percentage"`` ; `maximum`: ``100`` = 100; `type`: ``"number"`` = "number" } |
| `properties.progress.description` | ``"Progress percentage"`` |
| `properties.progress.maximum` | ``100`` |
| `properties.progress.type` | ``"number"`` |
| `properties.reason` | \{ `description`: ``"Reason for current state"`` ; `type`: ``"string"`` = "string" } |
| `properties.reason.description` | ``"Reason for current state"`` |
| `properties.reason.type` | ``"string"`` |
| `properties.state` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.state.isRequired` | ``true`` |
| `properties.state.type` | ``"Enum"`` |
| `properties.updated_at` | \{ `description`: ``"Job updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"Job updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$JobStatus.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$JobStatus.ts#L5)

___

### $Memory

• `Const` **$Memory**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `agent_id`: \{ `description`: ``"ID of the agent"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `content`: \{ `description`: ``"Content of the memory"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Memory created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `entities`: \{ `contains`: \{ `properties`: {} = \{} } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } ; `id`: \{ `description`: ``"Memory id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `last_accessed_at`: \{ `description`: ``"Memory last accessed at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `sentiment`: \{ `description`: ``"Sentiment (valence) of the memory on a scale of -1 to 1"`` ; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } ; `timestamp`: \{ `description`: ``"Memory happened at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `user_id`: \{ `description`: ``"ID of the user"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.agent_id` | \{ `description`: ``"ID of the agent"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.agent_id.description` | ``"ID of the agent"`` |
| `properties.agent_id.format` | ``"uuid"`` |
| `properties.agent_id.isRequired` | ``true`` |
| `properties.agent_id.type` | ``"string"`` |
| `properties.content` | \{ `description`: ``"Content of the memory"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.content.description` | ``"Content of the memory"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Memory created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Memory created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.entities` | \{ `contains`: \{ `properties`: {} = \{} } ; `isRequired`: ``true`` = true; `type`: ``"array"`` = "array" } |
| `properties.entities.contains` | \{ `properties`: {} = \{} } |
| `properties.entities.contains.properties` | {} |
| `properties.entities.isRequired` | ``true`` |
| `properties.entities.type` | ``"array"`` |
| `properties.id` | \{ `description`: ``"Memory id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Memory id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.last_accessed_at` | \{ `description`: ``"Memory last accessed at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.last_accessed_at.description` | ``"Memory last accessed at (RFC-3339 format)"`` |
| `properties.last_accessed_at.format` | ``"date-time"`` |
| `properties.last_accessed_at.type` | ``"string"`` |
| `properties.sentiment` | \{ `description`: ``"Sentiment (valence) of the memory on a scale of -1 to 1"`` ; `maximum`: ``1`` = 1; `minimum`: ``-1`` = -1; `type`: ``"number"`` = "number" } |
| `properties.sentiment.description` | ``"Sentiment (valence) of the memory on a scale of -1 to 1"`` |
| `properties.sentiment.maximum` | ``1`` |
| `properties.sentiment.minimum` | ``-1`` |
| `properties.sentiment.type` | ``"number"`` |
| `properties.timestamp` | \{ `description`: ``"Memory happened at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.timestamp.description` | ``"Memory happened at (RFC-3339 format)"`` |
| `properties.timestamp.format` | ``"date-time"`` |
| `properties.timestamp.type` | ``"string"`` |
| `properties.user_id` | \{ `description`: ``"ID of the user"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.user_id.description` | ``"ID of the user"`` |
| `properties.user_id.format` | ``"uuid"`` |
| `properties.user_id.isRequired` | ``true`` |
| `properties.user_id.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Memory.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$Memory.ts#L5)

___

### $MemoryAccessOptions

• `Const` **$MemoryAccessOptions**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `recall`: \{ `description`: ``"Whether previous memories should be recalled or not"`` ; `type`: ``"boolean"`` = "boolean" } ; `record`: \{ `description`: ``"Whether this interaction should be recorded in history or not"`` ; `type`: ``"boolean"`` = "boolean" } ; `remember`: \{ `description`: ``"Whether this interaction should form memories or not"`` ; `type`: ``"boolean"`` = "boolean" }  } |
| `properties.recall` | \{ `description`: ``"Whether previous memories should be recalled or not"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.recall.description` | ``"Whether previous memories should be recalled or not"`` |
| `properties.recall.type` | ``"boolean"`` |
| `properties.record` | \{ `description`: ``"Whether this interaction should be recorded in history or not"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.record.description` | ``"Whether this interaction should be recorded in history or not"`` |
| `properties.record.type` | ``"boolean"`` |
| `properties.remember` | \{ `description`: ``"Whether this interaction should form memories or not"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.remember.description` | ``"Whether this interaction should form memories or not"`` |
| `properties.remember.type` | ``"boolean"`` |

#### Defined in

[src/api/schemas/$MemoryAccessOptions.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$MemoryAccessOptions.ts#L5)

___

### $NamedToolChoice

• `Const` **$NamedToolChoice**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"Specifies a tool the model should use. Use to force the model to call a specific function."`` |
| `properties` | \{ `function`: \{ `isRequired`: ``true`` = true; `properties`: \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  }  } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.function` | \{ `isRequired`: ``true`` = true; `properties`: \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  }  } |
| `properties.function.isRequired` | ``true`` |
| `properties.function.properties` | \{ `name`: \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.function.properties.name` | \{ `description`: ``"The name of the function to call."`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.function.properties.name.description` | ``"The name of the function to call."`` |
| `properties.function.properties.name.isRequired` | ``true`` |
| `properties.function.properties.name.type` | ``"string"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$NamedToolChoice.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$NamedToolChoice.ts#L5)

___

### $PartialFunctionDef

• `Const` **$PartialFunctionDef**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `description`: \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `type`: ``"string"`` = "string" } ; `parameters`: \{ `description`: ``"Parameters accepeted by this function"`` ; `type`: ``"FunctionParameters"`` = "FunctionParameters" }  } |
| `properties.description` | \{ `description`: ``"A description of what the function does, used by the model to choose when and how to call the function."`` ; `type`: ``"string"`` = "string" } |
| `properties.description.description` | ``"A description of what the function does, used by the model to choose when and how to call the function."`` |
| `properties.description.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64."`` |
| `properties.name.type` | ``"string"`` |
| `properties.parameters` | \{ `description`: ``"Parameters accepeted by this function"`` ; `type`: ``"FunctionParameters"`` = "FunctionParameters" } |
| `properties.parameters.description` | ``"Parameters accepeted by this function"`` |
| `properties.parameters.type` | ``"FunctionParameters"`` |

#### Defined in

[src/api/schemas/$PartialFunctionDef.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$PartialFunctionDef.ts#L5)

___

### $PatchAgentRequest

• `Const` **$PatchAgentRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A request for patching an agent"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } ; `default_settings`: \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } ; `instructions`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `model`: \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the agent"`` ; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the agent"`` |
| `properties.about.type` | ``"string"`` |
| `properties.default_settings` | \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } |
| `properties.default_settings.description` | ``"Default model settings to start every session with"`` |
| `properties.default_settings.type` | ``"AgentDefaultSettings"`` |
| `properties.instructions` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.instructions.contains` | readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.instructions.description` | ``"Instructions for the agent"`` |
| `properties.instructions.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.model` | \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } |
| `properties.model.description` | ``"Name of the model that the agent is supposed to use"`` |
| `properties.model.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the agent"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the agent"`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$PatchAgentRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$PatchAgentRequest.ts#L5)

___

### $PatchSessionRequest

• `Const` **$PatchSessionRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A request for patching a session"`` |
| `properties` | \{ `context_overflow`: \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `situation`: \{ `description`: ``"Updated situation for this session"`` ; `type`: ``"string"`` = "string" } ; `token_budget`: \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" }  } |
| `properties.context_overflow` | \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } |
| `properties.context_overflow.description` | ``"Action to start on context window overflow"`` |
| `properties.context_overflow.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.situation` | \{ `description`: ``"Updated situation for this session"`` ; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"Updated situation for this session"`` |
| `properties.situation.type` | ``"string"`` |
| `properties.token_budget` | \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" } |
| `properties.token_budget.description` | ``"Threshold value for the adaptive context functionality"`` |
| `properties.token_budget.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$PatchSessionRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$PatchSessionRequest.ts#L5)

___

### $PatchToolRequest

• `Const` **$PatchToolRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `function`: \{ `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"PartialFunctionDef"`` = "PartialFunctionDef" }  } |
| `properties.function` | \{ `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"PartialFunctionDef"`` = "PartialFunctionDef" } |
| `properties.function.description` | ``"Function definition and parameters"`` |
| `properties.function.isRequired` | ``true`` |
| `properties.function.type` | ``"PartialFunctionDef"`` |

#### Defined in

[src/api/schemas/$PatchToolRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$PatchToolRequest.ts#L5)

___

### $PatchUserRequest

• `Const` **$PatchUserRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A request for patching a user"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$PatchUserRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$PatchUserRequest.ts#L5)

___

### $ResourceCreatedResponse

• `Const` **$ResourceCreatedResponse**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `created_at`: \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `id`: \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `jobs`: \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }  } |
| `properties.created_at` | \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.isRequired` | ``true`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.jobs` | \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } |
| `properties.jobs.contains` | \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.jobs.contains.format` | ``"uuid"`` |
| `properties.jobs.contains.type` | ``"string"`` |
| `properties.jobs.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$ResourceCreatedResponse.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ResourceCreatedResponse.ts#L5)

___

### $ResourceDeletedResponse

• `Const` **$ResourceDeletedResponse**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `deleted_at`: \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `id`: \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `jobs`: \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }  } |
| `properties.deleted_at` | \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.deleted_at.format` | ``"date-time"`` |
| `properties.deleted_at.isRequired` | ``true`` |
| `properties.deleted_at.type` | ``"string"`` |
| `properties.id` | \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.jobs` | \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } |
| `properties.jobs.contains` | \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.jobs.contains.format` | ``"uuid"`` |
| `properties.jobs.contains.type` | ``"string"`` |
| `properties.jobs.type` | ``"array"`` |

#### Defined in

[src/api/schemas/$ResourceDeletedResponse.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ResourceDeletedResponse.ts#L5)

___

### $ResourceUpdatedResponse

• `Const` **$ResourceUpdatedResponse**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `id`: \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `jobs`: \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } ; `updated_at`: \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.id` | \{ `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.jobs` | \{ `contains`: \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" } |
| `properties.jobs.contains` | \{ `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.jobs.contains.format` | ``"uuid"`` |
| `properties.jobs.contains.type` | ``"string"`` |
| `properties.jobs.type` | ``"array"`` |
| `properties.updated_at` | \{ `format`: ``"date-time"`` = "date-time"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.isRequired` | ``true`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$ResourceUpdatedResponse.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ResourceUpdatedResponse.ts#L5)

___

### $Session

• `Const` **$Session**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `agent_id`: \{ `description`: ``"Agent ID of agent associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `context_overflow`: \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Session created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"Session id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `render_templates`: \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } ; `situation`: \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } ; `summary`: \{ `description`: ``"(null at the beginning) - generated automatically after every interaction"`` ; `type`: ``"string"`` = "string" } ; `token_budget`: \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" } ; `updated_at`: \{ `description`: ``"Session updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `user_id`: \{ `description`: ``"User ID of user associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" }  } |
| `properties.agent_id` | \{ `description`: ``"Agent ID of agent associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.agent_id.description` | ``"Agent ID of agent associated with this session"`` |
| `properties.agent_id.format` | ``"uuid"`` |
| `properties.agent_id.isRequired` | ``true`` |
| `properties.agent_id.type` | ``"string"`` |
| `properties.context_overflow` | \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } |
| `properties.context_overflow.description` | ``"Action to start on context window overflow"`` |
| `properties.context_overflow.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Session created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Session created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"Session id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Session id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.render_templates` | \{ `description`: ``"Render system and assistant message content as jinja templates"`` ; `type`: ``"boolean"`` = "boolean" } |
| `properties.render_templates.description` | ``"Render system and assistant message content as jinja templates"`` |
| `properties.render_templates.type` | ``"boolean"`` |
| `properties.situation` | \{ `description`: ``"A specific situation that sets the background for this session"`` ; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"A specific situation that sets the background for this session"`` |
| `properties.situation.type` | ``"string"`` |
| `properties.summary` | \{ `description`: ``"(null at the beginning) - generated automatically after every interaction"`` ; `type`: ``"string"`` = "string" } |
| `properties.summary.description` | ``"(null at the beginning) - generated automatically after every interaction"`` |
| `properties.summary.type` | ``"string"`` |
| `properties.token_budget` | \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" } |
| `properties.token_budget.description` | ``"Threshold value for the adaptive context functionality"`` |
| `properties.token_budget.type` | ``"number"`` |
| `properties.updated_at` | \{ `description`: ``"Session updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"Session updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |
| `properties.user_id` | \{ `description`: ``"User ID of user associated with this session"`` ; `format`: ``"uuid"`` = "uuid"; `type`: ``"string"`` = "string" } |
| `properties.user_id.description` | ``"User ID of user associated with this session"`` |
| `properties.user_id.format` | ``"uuid"`` |
| `properties.user_id.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$Session.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$Session.ts#L5)

___

### $Suggestion

• `Const` **$Suggestion**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `description`: ``"The content of the suggestion"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"Suggestion created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `message_id`: \{ `description`: ``"The message that produced it"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `session_id`: \{ `description`: ``"Session this suggestion belongs to"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `target`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.content` | \{ `description`: ``"The content of the suggestion"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.content.description` | ``"The content of the suggestion"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"Suggestion created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"Suggestion created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.message_id` | \{ `description`: ``"The message that produced it"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.message_id.description` | ``"The message that produced it"`` |
| `properties.message_id.format` | ``"uuid"`` |
| `properties.message_id.isRequired` | ``true`` |
| `properties.message_id.type` | ``"string"`` |
| `properties.session_id` | \{ `description`: ``"Session this suggestion belongs to"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.session_id.description` | ``"Session this suggestion belongs to"`` |
| `properties.session_id.format` | ``"uuid"`` |
| `properties.session_id.isRequired` | ``true`` |
| `properties.session_id.type` | ``"string"`` |
| `properties.target` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.target.isRequired` | ``true`` |
| `properties.target.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$Suggestion.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$Suggestion.ts#L5)

___

### $Tool

• `Const` **$Tool**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `function`: \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } ; `id`: \{ `description`: ``"Tool ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `type`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.function` | \{ `contains`: readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] ; `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"one-of"`` = "one-of" } |
| `properties.function.contains` | readonly [\{ `type`: ``"FunctionDef"`` = "FunctionDef" }] |
| `properties.function.description` | ``"Function definition and parameters"`` |
| `properties.function.isRequired` | ``true`` |
| `properties.function.type` | ``"one-of"`` |
| `properties.id` | \{ `description`: ``"Tool ID"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"Tool ID"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.type` | \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" } |
| `properties.type.isRequired` | ``true`` |
| `properties.type.type` | ``"Enum"`` |

#### Defined in

[src/api/schemas/$Tool.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$Tool.ts#L5)

___

### $ToolChoiceOption

• `Const` **$ToolChoiceOption**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `contains` | readonly [\{ `type`: ``"Enum"`` = "Enum" }, \{ `type`: ``"NamedToolChoice"`` = "NamedToolChoice" }] |
| `description` | ``"Controls which (if any) function is called by the model.\n  `none` means the model will not call a function and instead generates a message.\n  `auto` means the model can pick between generating a message or calling a function.\n  Specifying a particular function via `{\"type: \"function\", \"function\": {\"name\": \"my_function\"}}` forces the model to call that function.\n  `none` is the default when no functions are present. `auto` is the default if functions are present.\n  "`` |
| `type` | ``"one-of"`` |

#### Defined in

[src/api/schemas/$ToolChoiceOption.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$ToolChoiceOption.ts#L5)

___

### $UpdateAgentRequest

• `Const` **$UpdateAgentRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for updating an agent"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `default_settings`: \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } ; `instructions`: \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `model`: \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } ; `name`: \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the agent"`` |
| `properties.about.isRequired` | ``true`` |
| `properties.about.type` | ``"string"`` |
| `properties.default_settings` | \{ `description`: ``"Default model settings to start every session with"`` ; `type`: ``"AgentDefaultSettings"`` = "AgentDefaultSettings" } |
| `properties.default_settings.description` | ``"Default model settings to start every session with"`` |
| `properties.default_settings.type` | ``"AgentDefaultSettings"`` |
| `properties.instructions` | \{ `contains`: readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] ; `description`: ``"Instructions for the agent"`` ; `type`: ``"one-of"`` = "one-of" } |
| `properties.instructions.contains` | readonly [\{ `type`: ``"string"`` = "string" }, \{ `contains`: \{ `type`: ``"string"`` = "string" } ; `type`: ``"array"`` = "array" }] |
| `properties.instructions.description` | ``"Instructions for the agent"`` |
| `properties.instructions.type` | ``"one-of"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.model` | \{ `description`: ``"Name of the model that the agent is supposed to use"`` ; `type`: ``"string"`` = "string" } |
| `properties.model.description` | ``"Name of the model that the agent is supposed to use"`` |
| `properties.model.type` | ``"string"`` |
| `properties.name` | \{ `description`: ``"Name of the agent"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the agent"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$UpdateAgentRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$UpdateAgentRequest.ts#L5)

___

### $UpdateSessionRequest

• `Const` **$UpdateSessionRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for updating a session"`` |
| `properties` | \{ `context_overflow`: \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `situation`: \{ `description`: ``"Updated situation for this session"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `token_budget`: \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" }  } |
| `properties.context_overflow` | \{ `description`: ``"Action to start on context window overflow"`` ; `type`: ``"string"`` = "string" } |
| `properties.context_overflow.description` | ``"Action to start on context window overflow"`` |
| `properties.context_overflow.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.situation` | \{ `description`: ``"Updated situation for this session"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.situation.description` | ``"Updated situation for this session"`` |
| `properties.situation.isRequired` | ``true`` |
| `properties.situation.type` | ``"string"`` |
| `properties.token_budget` | \{ `description`: ``"Threshold value for the adaptive context functionality"`` ; `type`: ``"number"`` = "number" } |
| `properties.token_budget.description` | ``"Threshold value for the adaptive context functionality"`` |
| `properties.token_budget.type` | ``"number"`` |

#### Defined in

[src/api/schemas/$UpdateSessionRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$UpdateSessionRequest.ts#L5)

___

### $UpdateToolRequest

• `Const` **$UpdateToolRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `function`: \{ `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"FunctionDef"`` = "FunctionDef" }  } |
| `properties.function` | \{ `description`: ``"Function definition and parameters"`` ; `isRequired`: ``true`` = true; `type`: ``"FunctionDef"`` = "FunctionDef" } |
| `properties.function.description` | ``"Function definition and parameters"`` |
| `properties.function.isRequired` | ``true`` |
| `properties.function.type` | ``"FunctionDef"`` |

#### Defined in

[src/api/schemas/$UpdateToolRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$UpdateToolRequest.ts#L5)

___

### $UpdateUserRequest

• `Const` **$UpdateUserRequest**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `description` | ``"A valid request payload for updating a user"`` |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.isRequired` | ``true`` |
| `properties.about.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"Optional metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"Optional metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.isRequired` | ``true`` |
| `properties.name.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$UpdateUserRequest.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$UpdateUserRequest.ts#L5)

___

### $User

• `Const` **$User**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `about`: \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } ; `created_at`: \{ `description`: ``"User created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } ; `id`: \{ `description`: ``"User id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `metadata`: \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } ; `name`: \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } ; `updated_at`: \{ `description`: ``"User updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" }  } |
| `properties.about` | \{ `description`: ``"About the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.about.description` | ``"About the user"`` |
| `properties.about.type` | ``"string"`` |
| `properties.created_at` | \{ `description`: ``"User created at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.created_at.description` | ``"User created at (RFC-3339 format)"`` |
| `properties.created_at.format` | ``"date-time"`` |
| `properties.created_at.type` | ``"string"`` |
| `properties.id` | \{ `description`: ``"User id (UUID)"`` ; `format`: ``"uuid"`` = "uuid"; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.id.description` | ``"User id (UUID)"`` |
| `properties.id.format` | ``"uuid"`` |
| `properties.id.isRequired` | ``true`` |
| `properties.id.type` | ``"string"`` |
| `properties.metadata` | \{ `description`: ``"(Optional) metadata"`` ; `properties`: {} = \{} } |
| `properties.metadata.description` | ``"(Optional) metadata"`` |
| `properties.metadata.properties` | {} |
| `properties.name` | \{ `description`: ``"Name of the user"`` ; `type`: ``"string"`` = "string" } |
| `properties.name.description` | ``"Name of the user"`` |
| `properties.name.type` | ``"string"`` |
| `properties.updated_at` | \{ `description`: ``"User updated at (RFC-3339 format)"`` ; `format`: ``"date-time"`` = "date-time"; `type`: ``"string"`` = "string" } |
| `properties.updated_at.description` | ``"User updated at (RFC-3339 format)"`` |
| `properties.updated_at.format` | ``"date-time"`` |
| `properties.updated_at.type` | ``"string"`` |

#### Defined in

[src/api/schemas/$User.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$User.ts#L5)

___

### $agent\_id

• `Const` **$agent\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$agent_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$agent_id.ts#L5)

___

### $doc\_id

• `Const` **$doc\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$doc_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$doc_id.ts#L5)

___

### $job\_id

• `Const` **$job\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$job_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$job_id.ts#L5)

___

### $memory\_id

• `Const` **$memory\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$memory_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$memory_id.ts#L5)

___

### $message\_id

• `Const` **$message\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$message_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$message_id.ts#L5)

___

### $session\_id

• `Const` **$session\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$session_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$session_id.ts#L5)

___

### $tool\_id

• `Const` **$tool\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$tool_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$tool_id.ts#L5)

___

### $user\_id

• `Const` **$user\_id**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `format` | ``"uuid"`` |
| `type` | ``"string"`` |

#### Defined in

[src/api/schemas/$user_id.ts:5](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/schemas/$user_id.ts#L5)

___

### OpenAPI

• `Const` **OpenAPI**: [`OpenAPIConfig`](api.md#openapiconfig)

#### Defined in

[src/api/core/OpenAPI.ts:22](https://github.com/julep-ai/julep/blob/227123c5f9d22b396d22945238105bcec56713cc/sdks/ts/src/api/core/OpenAPI.ts#L22)
