[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/CreateToolRequest

# Module: api/models/CreateToolRequest

## Table of contents

### Type Aliases

- [CreateToolRequest](api_models_CreateToolRequest.md#createtoolrequest)

## Type Aliases

### CreateToolRequest

Ƭ **CreateToolRequest**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `function` | [`FunctionDef`](api_models_FunctionDef.md#functiondef) | Function definition and parameters |
| `type` | ``"function"`` \| ``"webhook"`` | Whether this tool is a `function` or a `webhook` (Only `function` tool supported right now) |

#### Defined in

[src/api/models/CreateToolRequest.ts:6](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/CreateToolRequest.ts#L6)
