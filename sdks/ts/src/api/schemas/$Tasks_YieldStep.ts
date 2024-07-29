/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_YieldStep = {
  properties: {
    workflow: {
      type: "string",
      description: `The subworkflow to run`,
      isRequired: true,
    },
    arguments: {
      type: "dictionary",
      contains: {
        type: "Common_PyExpression",
      },
      isRequired: true,
    },
  },
} as const;
