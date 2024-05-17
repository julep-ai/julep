[@julep/sdk](../README.md) / [Exports](../modules.md) / api/schemas/$InputChatMLMessage

# Module: api/schemas/$InputChatMLMessage

## Table of contents

### Variables

- [$InputChatMLMessage](api_schemas__InputChatMLMessage.md#$inputchatmlmessage)

## Variables

### $InputChatMLMessage

• `Const` **$InputChatMLMessage**: `Object`

#### Type declaration

| Name | Type |
| :------ | :------ |
| `properties` | \{ `content`: \{ `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } ; `continue`: \{ `description`: ``"Whether to continue this message or return a new one"`` ; `type`: ``"boolean"`` = "boolean" } ; `name`: \{ `description`: ``"ChatML name"`` ; `type`: ``"string"`` = "string" } ; `role`: \{ `isRequired`: ``true`` = true; `type`: ``"Enum"`` = "Enum" }  } |
| `properties.content` | \{ `description`: ``"ChatML content"`` ; `isRequired`: ``true`` = true; `type`: ``"string"`` = "string" } |
| `properties.content.description` | ``"ChatML content"`` |
| `properties.content.isRequired` | ``true`` |
| `properties.content.type` | ``"string"`` |
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

[src/api/schemas/$InputChatMLMessage.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/schemas/$InputChatMLMessage.ts#L5)
