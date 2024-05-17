[@julep/sdk](../README.md) / [Exports](../modules.md) / api/models/JobStatus

# Module: api/models/JobStatus

## Table of contents

### Type Aliases

- [JobStatus](api_models_JobStatus.md#jobstatus)

## Type Aliases

### JobStatus

Ƭ **JobStatus**: `Object`

#### Type declaration

| Name | Type | Description |
| :------ | :------ | :------ |
| `created_at` | `string` | Job created at (RFC-3339 format) |
| `has_progress?` | `boolean` | Whether this Job supports progress updates |
| `id` | `string` | Job id (UUID) |
| `name` | `string` | Name of the job |
| `progress?` | `number` | Progress percentage |
| `reason?` | `string` | Reason for current state |
| `state` | ``"pending"`` \| ``"in_progress"`` \| ``"retrying"`` \| ``"succeeded"`` \| ``"aborted"`` \| ``"failed"`` \| ``"unknown"`` | Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed) |
| `updated_at?` | `string` | Job updated at (RFC-3339 format) |

#### Defined in

[src/api/models/JobStatus.ts:5](https://github.com/julep-ai/julep/blob/035e7f91b35da5c19151875490e535b6923a07fe/sdks/ts/src/api/models/JobStatus.ts#L5)
