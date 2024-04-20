[@julep/sdk](../README.md) / [Modules](../modules.md) / utils/isValidUuid4

# Module: utils/isValidUuid4

## Table of contents

### Functions

- [isValidUuid4](utils_isValidUuid4.md#isvaliduuid4)

## Functions

### isValidUuid4

▸ **isValidUuid4**(`uuidToTest`): `boolean`

Validates if the input string is a valid UUID v4.
This function performs a two-step validation process:
1. Validates the format of the UUID using `uuidValidate`.
2. Checks that the version of the UUID is 4 using `uuidVersion`.

#### Parameters

| Name | Type | Description |
| :------ | :------ | :------ |
| `uuidToTest` | `string` | The string to test for a valid UUID v4. |

#### Returns

`boolean`

True if the input is a valid UUID v4, otherwise false.

#### Defined in

[src/utils/isValidUuid4.ts:11](https://github.com/julep-ai/julep/blob/411d5c610ac77f3e9c57ab269fe4f1b543ed4b7a/sdks/ts/src/utils/isValidUuid4.ts#L11)
