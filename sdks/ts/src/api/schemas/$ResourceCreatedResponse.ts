/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ResourceCreatedResponse = {
  properties: {
    id: {
      type: 'string',
      isRequired: true,
      format: 'uuid',
    },
    created_at: {
      type: 'string',
      isRequired: true,
      format: 'date-time',
    },
    jobs: {
      type: 'array',
      contains: {
        type: 'string',
        format: 'uuid',
      },
    },
  },
} as const;
