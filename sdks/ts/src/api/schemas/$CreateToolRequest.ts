/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $CreateToolRequest = {
  properties: {
    type: {
      type: 'Enum',
      isRequired: true,
    },
    function: {
      type: 'one-of',
      description: `Function definition and parameters`,
      contains: [{
        type: 'FunctionDef',
      }],
      isRequired: true,
    },
  },
} as const;
