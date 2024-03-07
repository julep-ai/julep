/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $InputChatMLMessage = {
  properties: {
    role: {
      type: 'Enum',
      isRequired: true,
    },
    content: {
      type: 'string',
      description: `ChatML content`,
      isRequired: true,
    },
    name: {
      type: 'string',
      description: `ChatML name`,
    },
    continue: {
      type: 'boolean',
      description: `Whether to continue this message or return a new one`,
    },
  },
} as const;
