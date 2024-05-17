[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/Tool

# Module: api/models/Tool

## Table of contents

### Type Aliases

- [Tool](api_models_Tool.md#tool)

## Type Aliases

### Tool

Ƭ **Tool**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | [`FunctionDef`](api_models_FunctionDef.md#functiondef) | Function definition and parameters |
| `id` | `string` | Tool ID |
| `type` | ``"function"`` \| ``"webhook"`` | Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now) |

#### Defined in

[src/api/models/Tool.ts:6](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/Tool.ts#L6)
