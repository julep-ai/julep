[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / FunctionDef

# Interface: FunctionDef

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).FunctionDef

## Table of contents

### Properties

- [description](index.JulepApi.FunctionDef.md#description)
- [name](index.JulepApi.FunctionDef.md#name)
- [parameters](index.JulepApi.FunctionDef.md#parameters)

## Properties

### description

• `Optional` **description**: `string`

A description of what the function does, used by the model to choose when and how to call the function.

#### Defined in

[src/api/api/types/FunctionDef.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/FunctionDef.d.ts#L7)

___

### name

• **name**: `string`

The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.

#### Defined in

[src/api/api/types/FunctionDef.d.ts:9](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/FunctionDef.d.ts#L9)

___

### parameters

• **parameters**: [`FunctionParameters`](../modules/index.JulepApi.md#functionparameters)

Parameters accepeted by this function

#### Defined in

[src/api/api/types/FunctionDef.d.ts:11](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/FunctionDef.d.ts#L11)
