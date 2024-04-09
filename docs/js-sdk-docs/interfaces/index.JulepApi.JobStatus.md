[@julep/sdk](../README.md) / [Modules](../modules.md) / [index](../modules/index.md) / [JulepApi](../modules/index.JulepApi.md) / JobStatus

# Interface: JobStatus

[index](../modules/index.md).[JulepApi](../modules/index.JulepApi.md).JobStatus

## Table of contents

### Properties

- [createdAt](index.JulepApi.JobStatus.md#createdat)
- [hasProgress](index.JulepApi.JobStatus.md#hasprogress)
- [id](index.JulepApi.JobStatus.md#id)
- [name](index.JulepApi.JobStatus.md#name)
- [progress](index.JulepApi.JobStatus.md#progress)
- [reason](index.JulepApi.JobStatus.md#reason)
- [state](index.JulepApi.JobStatus.md#state)
- [updatedAt](index.JulepApi.JobStatus.md#updatedat)

## Properties

### createdAt

• **createdAt**: `Date`

Job created at (RFC-3339 format)

#### Defined in

[src/api/api/types/JobStatus.d.ts:11](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L11)

___

### hasProgress

• `Optional` **hasProgress**: `boolean`

Whether this Job supports progress updates

#### Defined in

[src/api/api/types/JobStatus.d.ts:17](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L17)

___

### id

• **id**: `string`

Job id (UUID)

#### Defined in

[src/api/api/types/JobStatus.d.ts:15](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L15)

___

### name

• **name**: `string`

Name of the job

#### Defined in

[src/api/api/types/JobStatus.d.ts:7](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L7)

___

### progress

• `Optional` **progress**: `number`

Progress percentage

#### Defined in

[src/api/api/types/JobStatus.d.ts:19](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L19)

___

### reason

• `Optional` **reason**: `string`

Reason for current state

#### Defined in

[src/api/api/types/JobStatus.d.ts:9](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L9)

___

### state

• **state**: [`JobStatusState`](../modules/index.JulepApi.md#jobstatusstate)

Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed)

#### Defined in

[src/api/api/types/JobStatus.d.ts:21](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L21)

___

### updatedAt

• `Optional` **updatedAt**: `Date`

Job updated at (RFC-3339 format)

#### Defined in

[src/api/api/types/JobStatus.d.ts:13](https://github.com/julep-ai/monorepo/blob/8b1493a/sdks/js/src/api/api/types/JobStatus.d.ts#L13)
