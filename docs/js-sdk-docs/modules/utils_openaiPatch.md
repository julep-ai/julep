[@julep/sdk](../README.md) / [Modules](../modules.md) / utils/openaiPatch

# Module: utils/openaiPatch

## Table of contents

### Functions

- [patchCreate](utils_openaiPatch.md#patchcreate)

## Functions

### patchCreate

▸ **patchCreate**(`client`, `scope?`): `any`

Patches the 'create' method of an OpenAI client instance to ensure a default model is used if none is specified.
This is useful for enforcing a consistent model usage across different parts of the SDK.

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `client` | `any` | `undefined` | The OpenAI client instance to be patched. |
| `scope` | `any` | `null` | Optional. The scope in which the original 'create' method is bound. Defaults to the client itself if not provided. |

#### Returns

`any`

#### Defined in

[src/utils/openaiPatch.ts:8](https://github.com/julep-ai/julep/blob/c703332acc3c978fec6732847b3d2cfd6d3b1330/sdks/ts/src/utils/openaiPatch.ts#L8)
