[@julep/sdk](../README.md) / [Modules](../modules.md) / [api/types/Suggestion](../modules/api_types_Suggestion.md) / Suggestion

# Interface: Suggestion

[api/types/Suggestion](../modules/api_types_Suggestion.md).Suggestion

## Table of contents

### Properties

- [content](api_types_Suggestion.Suggestion.md#content)
- [createdAt](api_types_Suggestion.Suggestion.md#createdat)
- [messageId](api_types_Suggestion.Suggestion.md#messageid)
- [sessionId](api_types_Suggestion.Suggestion.md#sessionid)
- [target](api_types_Suggestion.Suggestion.md#target)

## Properties

### content

• **content**: `string`

The content of the suggestion

#### Defined in

[src/api/api/types/Suggestion.d.ts:11](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Suggestion.d.ts#L11)

___

### createdAt

• `Optional` **createdAt**: `Date`

Suggestion created at (RFC-3339 format)

#### Defined in

[src/api/api/types/Suggestion.d.ts:7](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Suggestion.d.ts#L7)

___

### messageId

• **messageId**: `string`

The message that produced it

#### Defined in

[src/api/api/types/Suggestion.d.ts:13](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Suggestion.d.ts#L13)

___

### sessionId

• **sessionId**: `string`

Session this suggestion belongs to

#### Defined in

[src/api/api/types/Suggestion.d.ts:15](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Suggestion.d.ts#L15)

___

### target

• **target**: [`SuggestionTarget`](../modules/api_types_SuggestionTarget.md#suggestiontarget)

Whether the suggestion is for the `agent` or a `user`

#### Defined in

[src/api/api/types/Suggestion.d.ts:9](https://github.com/julep-ai/samantha-monorepo/blob/9aefd53/sdks/js/src/api/api/types/Suggestion.d.ts#L9)
