[@julep/sdk](../README.md) / [Modules](../modules.md) / [serialization/client/requests/ChatInput](../modules/serialization_client_requests_ChatInput.md) / [ChatInput](../modules/serialization_client_requests_ChatInput.ChatInput.md) / Raw

# Interface: Raw

[serialization/client/requests/ChatInput](../modules/serialization_client_requests_ChatInput.md).[ChatInput](../modules/serialization_client_requests_ChatInput.ChatInput.md).Raw

## Hierarchy

- [`Raw`](serialization_types_ChatInputData.ChatInputData.Raw.md)

- [`Raw`](serialization_types_ChatSettings.ChatSettings.Raw.md)

- [`Raw`](serialization_types_MemoryAccessOptions.MemoryAccessOptions.Raw.md)

  ↳ **`Raw`**

## Table of contents

### Properties

- [frequency\_penalty](serialization_client_requests_ChatInput.ChatInput.Raw.md#frequency_penalty)
- [length\_penalty](serialization_client_requests_ChatInput.ChatInput.Raw.md#length_penalty)
- [logit\_bias](serialization_client_requests_ChatInput.ChatInput.Raw.md#logit_bias)
- [max\_tokens](serialization_client_requests_ChatInput.ChatInput.Raw.md#max_tokens)
- [messages](serialization_client_requests_ChatInput.ChatInput.Raw.md#messages)
- [presence\_penalty](serialization_client_requests_ChatInput.ChatInput.Raw.md#presence_penalty)
- [recall](serialization_client_requests_ChatInput.ChatInput.Raw.md#recall)
- [remember](serialization_client_requests_ChatInput.ChatInput.Raw.md#remember)
- [repetition\_penalty](serialization_client_requests_ChatInput.ChatInput.Raw.md#repetition_penalty)
- [response\_format](serialization_client_requests_ChatInput.ChatInput.Raw.md#response_format)
- [seed](serialization_client_requests_ChatInput.ChatInput.Raw.md#seed)
- [stop](serialization_client_requests_ChatInput.ChatInput.Raw.md#stop)
- [stream](serialization_client_requests_ChatInput.ChatInput.Raw.md#stream)
- [temperature](serialization_client_requests_ChatInput.ChatInput.Raw.md#temperature)
- [tool\_choice](serialization_client_requests_ChatInput.ChatInput.Raw.md#tool_choice)
- [tools](serialization_client_requests_ChatInput.ChatInput.Raw.md#tools)
- [top\_p](serialization_client_requests_ChatInput.ChatInput.Raw.md#top_p)

## Properties

### frequency\_penalty

• `Optional` **frequency\_penalty**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[frequency_penalty](serialization_types_ChatSettings.ChatSettings.Raw.md#frequency_penalty)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L13)

___

### length\_penalty

• `Optional` **length\_penalty**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[length_penalty](serialization_types_ChatSettings.ChatSettings.Raw.md#length_penalty)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:14](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L14)

___

### logit\_bias

• `Optional` **logit\_bias**: ``null`` \| `Record`\<`string`, `undefined` \| ``null`` \| `number`\>

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[logit_bias](serialization_types_ChatSettings.ChatSettings.Raw.md#logit_bias)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L15)

___

### max\_tokens

• `Optional` **max\_tokens**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[max_tokens](serialization_types_ChatSettings.ChatSettings.Raw.md#max_tokens)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:16](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L16)

___

### messages

• **messages**: [`Raw`](serialization_types_InputChatMlMessage.InputChatMlMessage.Raw.md)[]

#### Inherited from

[Raw](serialization_types_ChatInputData.ChatInputData.Raw.md).[messages](serialization_types_ChatInputData.ChatInputData.Raw.md#messages)

#### Defined in

[src/api/serialization/types/ChatInputData.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatInputData.d.ts#L13)

___

### presence\_penalty

• `Optional` **presence\_penalty**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[presence_penalty](serialization_types_ChatSettings.ChatSettings.Raw.md#presence_penalty)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:17](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L17)

___

### recall

• `Optional` **recall**: ``null`` \| `boolean`

#### Inherited from

[Raw](serialization_types_MemoryAccessOptions.MemoryAccessOptions.Raw.md).[recall](serialization_types_MemoryAccessOptions.MemoryAccessOptions.Raw.md#recall)

#### Defined in

[src/api/serialization/types/MemoryAccessOptions.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/MemoryAccessOptions.d.ts#L13)

___

### remember

• `Optional` **remember**: ``null`` \| `boolean`

#### Inherited from

[Raw](serialization_types_MemoryAccessOptions.MemoryAccessOptions.Raw.md).[remember](serialization_types_MemoryAccessOptions.MemoryAccessOptions.Raw.md#remember)

#### Defined in

[src/api/serialization/types/MemoryAccessOptions.d.ts:14](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/MemoryAccessOptions.d.ts#L14)

___

### repetition\_penalty

• `Optional` **repetition\_penalty**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[repetition_penalty](serialization_types_ChatSettings.ChatSettings.Raw.md#repetition_penalty)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:18](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L18)

___

### response\_format

• `Optional` **response\_format**: ``null`` \| [`Raw`](serialization_types_ChatSettingsResponseFormat.ChatSettingsResponseFormat.Raw.md)

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[response_format](serialization_types_ChatSettings.ChatSettings.Raw.md#response_format)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:19](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L19)

___

### seed

• `Optional` **seed**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[seed](serialization_types_ChatSettings.ChatSettings.Raw.md#seed)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:20](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L20)

___

### stop

• `Optional` **stop**: [`Raw`](../modules/serialization_types_ChatSettingsStop.ChatSettingsStop.md#raw)

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[stop](serialization_types_ChatSettings.ChatSettings.Raw.md#stop)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:21](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L21)

___

### stream

• `Optional` **stream**: ``null`` \| `boolean`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[stream](serialization_types_ChatSettings.ChatSettings.Raw.md#stream)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:22](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L22)

___

### temperature

• `Optional` **temperature**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[temperature](serialization_types_ChatSettings.ChatSettings.Raw.md#temperature)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:23](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L23)

___

### tool\_choice

• `Optional` **tool\_choice**: ``null`` \| `string`

#### Inherited from

[Raw](serialization_types_ChatInputData.ChatInputData.Raw.md).[tool_choice](serialization_types_ChatInputData.ChatInputData.Raw.md#tool_choice)

#### Defined in

[src/api/serialization/types/ChatInputData.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatInputData.d.ts#L15)

___

### tools

• `Optional` **tools**: ``null`` \| [`Raw`](serialization_types_Tool.Tool.Raw.md)[]

#### Inherited from

[Raw](serialization_types_ChatInputData.ChatInputData.Raw.md).[tools](serialization_types_ChatInputData.ChatInputData.Raw.md#tools)

#### Defined in

[src/api/serialization/types/ChatInputData.d.ts:14](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatInputData.d.ts#L14)

___

### top\_p

• `Optional` **top\_p**: ``null`` \| `number`

#### Inherited from

[Raw](serialization_types_ChatSettings.ChatSettings.Raw.md).[top_p](serialization_types_ChatSettings.ChatSettings.Raw.md#top_p)

#### Defined in

[src/api/serialization/types/ChatSettings.d.ts:24](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/serialization/types/ChatSettings.d.ts#L24)
