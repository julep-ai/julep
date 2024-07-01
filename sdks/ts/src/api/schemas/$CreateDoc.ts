/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $CreateDoc = {
  properties: {
    title: {
      type: "string",
      description: `Title describing what this bit of information contains`,
      isRequired: true,
    },
    content: {
      type: "one-of",
      description: `Information content`,
      contains: [
        {
          type: "array",
          contains: {
            type: "string",
            minItems: 1,
          },
        },
        {
          type: "string",
          description: `A single document chunk`,
        },
      ],
      isRequired: true,
    },
    metadata: {
      description: `Optional metadata`,
      properties: {},
    },
  },
} as const;
