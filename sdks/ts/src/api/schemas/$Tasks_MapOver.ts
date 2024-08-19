/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_MapOver = {
  properties: {
    over: {
      type: "all-of",
      description: `The variable to iterate over`,
      contains: [
        {
          type: "Common_PyExpression",
        },
      ],
      isRequired: true,
    },
    workflow: {
      type: "string",
      description: `The subworkflow to run for each iteration`,
      isRequired: true,
    },
  },
} as const;
