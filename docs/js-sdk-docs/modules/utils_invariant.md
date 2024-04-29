[@julep/sdk](../README.md) / [Modules](../modules.md) / utils/invariant

# Module: utils/invariant

## Table of contents

### Functions

- [invariant](utils_invariant.md#invariant)

## Functions

### invariant

▸ **invariant**(`condition`, `message?`): `void`

Ensures that a condition is met, throwing a custom error message if not.

#### Parameters

| Name | Type | Default value | Description |
| :------ | :------ | :------ | :------ |
| `condition` | `any` | `undefined` | The condition to test. If falsy, an error is thrown. |
| `message` | `string` | `"Invariant Violation"` | Optional. The error message to throw if the condition is not met. Defaults to "Invariant Violation". |

#### Returns

`void`

#### Defined in

[src/utils/invariant.ts:6](https://github.com/julep-ai/julep/blob/2427a5e8467e0e6e24dfb9b44e47b5c6ab06feb8/sdks/ts/src/utils/invariant.ts#L6)
