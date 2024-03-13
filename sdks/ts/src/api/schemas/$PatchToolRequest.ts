/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $PatchToolRequest = {
  properties: {
    function: {
      type: "one-of",
      description: `Function definition and parameters`,
      contains: [
        {
          type: "FunctionDef",
        },
      ],
      isRequired: true,
    },
  },
} as const;
