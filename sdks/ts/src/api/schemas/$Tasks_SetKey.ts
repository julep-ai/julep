/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_SetKey = {
  properties: {
    key: {
      type: "string",
      description: `The key to set`,
      isRequired: true,
    },
    value: {
      type: "all-of",
      description: `The value to set`,
      contains: [
        {
          type: "Common_PyExpression",
        },
      ],
      isRequired: true,
    },
  },
} as const;
