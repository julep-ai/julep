[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / Suggestion

# Interface: Suggestion

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).Suggestion

## Table of contents

### Properties

- [content](index.JulepApi.Suggestion.md#content)
- [createdAt](index.JulepApi.Suggestion.md#createdat)
- [messageId](index.JulepApi.Suggestion.md#messageid)
- [sessionId](index.JulepApi.Suggestion.md#sessionid)
- [target](index.JulepApi.Suggestion.md#target)

## Properties

### content

• **content**: `string`

The content of the suggestion

#### Defined in

[src/api/api/types/Suggestion.d.ts:11](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Suggestion.d.ts#L11)

___

### createdAt

• `Optional` **createdAt**: `Date`

Suggestion created at (RFC-3339 format)

#### Defined in

[src/api/api/types/Suggestion.d.ts:7](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Suggestion.d.ts#L7)

___

### messageId

• **messageId**: `string`

The message that produced it

#### Defined in

[src/api/api/types/Suggestion.d.ts:13](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Suggestion.d.ts#L13)

___

### sessionId

• **sessionId**: `string`

Session this suggestion belongs to

#### Defined in

[src/api/api/types/Suggestion.d.ts:15](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Suggestion.d.ts#L15)

___

### target

• **target**: [`SuggestionTarget`](../modules/index.JulepApi.md#suggestiontarget)

Whether the suggestion is for the `agent` or a `user`

#### Defined in

[src/api/api/types/Suggestion.d.ts:9](https://github.com/julep-ai/samantha-dev/blob/1a65618/sdks/js/src/api/api/types/Suggestion.d.ts#L9)
