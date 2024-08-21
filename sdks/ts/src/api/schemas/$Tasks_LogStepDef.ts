/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export const $Tasks_LogStepDef = {
  properties: {
    log: {
      type: "all-of",
      description: `The value to log`,
      contains: [
        {
          type: "Common_PyExpression",
        },
      ],
      isRequired: true,
    },
  },
} as const;
