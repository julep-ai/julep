/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $ResourceDeletedResponse = {
  properties: {
    id: {
      type: 'string',
      isRequired: true,
      format: 'uuid',
    },
    deleted_at: {
      type: 'string',
      isRequired: true,
      format: 'date-time',
    },
  },
} as const;
