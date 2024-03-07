/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $JobStatus = {
  properties: {
    name: {
      type: 'string',
      description: `Name of the job`,
      isRequired: true,
    },
    reason: {
      type: 'string',
      description: `Reason for current state`,
    },
    created_at: {
      type: 'string',
      description: `Job created at (RFC-3339 format)`,
      isRequired: true,
      format: 'date-time',
    },
    updated_at: {
      type: 'string',
      description: `Job updated at (RFC-3339 format)`,
      format: 'date-time',
    },
    id: {
      type: 'string',
      description: `Job id (UUID)`,
      isRequired: true,
      format: 'uuid',
    },
    has_progress: {
      type: 'boolean',
      description: `Whether this Job supports progress updates`,
    },
    progress: {
      type: 'number',
      description: `Progress percentage`,
      maximum: 100,
    },
    state: {
      type: 'Enum',
      isRequired: true,
    },
  },
} as const;
