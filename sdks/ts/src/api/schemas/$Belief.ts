/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Belief = {
  properties: {
    type: {
      type: 'Enum',
      isRequired: true,
    },
    subject: {
      type: 'string',
      description: `(Optional) ID of the subject user`,
      format: 'uuid',
    },
    content: {
      type: 'string',
      description: `Content of the memory`,
      isRequired: true,
    },
    rationale: {
      type: 'string',
      description: `Rationale: Why did the model decide to form this memory`,
    },
    weight: {
      type: 'number',
      description: `Weight (importance) of the memory on a scale of 0-100`,
      isRequired: true,
      maximum: 100,
    },
    sentiment: {
      type: 'number',
      description: `Sentiment (valence) of the memory on a scale of -1 to 1`,
      isRequired: true,
      maximum: 1,
      minimum: -1,
    },
    created_at: {
      type: 'string',
      description: `Belief created at (RFC-3339 format)`,
      isRequired: true,
      format: 'date-time',
    },
    id: {
      type: 'string',
      description: `Belief id (UUID)`,
      isRequired: true,
      format: 'uuid',
    },
  },
} as const;
