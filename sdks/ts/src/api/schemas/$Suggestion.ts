/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Suggestion = {
  properties: {
    created_at: {
      type: 'string',
      description: `Suggestion created at (RFC-3339 format)`,
      format: 'date-time',
    },
    target: {
      type: 'Enum',
      isRequired: true,
    },
    content: {
      type: 'string',
      description: `The content of the suggestion`,
      isRequired: true,
    },
    message_id: {
      type: 'string',
      description: `The message that produced it`,
      isRequired: true,
      format: 'uuid',
    },
    session_id: {
      type: 'string',
      description: `Session this suggestion belongs to`,
      isRequired: true,
      format: 'uuid',
    },
  },
} as const;
